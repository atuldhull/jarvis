"""The Master Orchestrator — JARVIS's CEO.

For an everyday message it just lets the general assistant answer (the fast path —
zero planning overhead). For a genuinely multi-step request it:

  1. PLANS a task graph — steps assigned to departments, with dependencies;
  2. EXECUTES it — independent steps run in PARALLEL on worker threads, dependent
     steps receive their prerequisites' outputs as context;
  3. AGGREGATES every result into one reply in JARVIS's voice.

Everything thinks through the model router, so the whole org runs on the local
brain today and upgrades to the cloud brains the moment keys are added.
"""

import concurrent.futures
import json
import re
import sys

import config
from brain.router import chat
from brain.jsonutil import extract_json
from agents.roster import make_agent, DEPARTMENTS, roster_brief
from memory.manager import MemoryManager


# ── Prompts (designed for strict, unambiguous JSON from a small local model) ───
PLAN_PROMPT = """You are the PLANNER stage of JARVIS. The request is COMPLEX. Break it into the SMALLEST correct set of steps and assign each to one department. Output STRICT JSON and nothing else — no prose, no markdown, no code fences, no comments, no trailing commas.

Departments (use these EXACT agent names, lowercase):
- research   -> web/browser investigation, gather + summarize info.
- software   -> read/write files and WRITE CODE (outputs code as TEXT; can save to a file).
- data       -> analyze files/CSV/JSON and produce SQL or analysis (outputs SQL/analysis as TEXT).
- browser    -> web/Chrome actions: open/click/type/read pages, youtube, whatsapp messaging.
- system     -> control the machine: open desktop apps, time/system info, lock/sleep/shutdown/restart.
- general    -> everyday answers, glue, simple tool use when no specialist fits.

HARD RULES:
1. Use the FEWEST steps that actually do the job. Prefer 2-4 steps. Never invent work the user didn't ask for. If two things can be one step for one agent, make them one step.
2. Each step is an object with EXACTLY these keys: "id" (a short lowercase string like "s1"), "agent" (one department name), "task" (a clear self-contained instruction the agent can run alone), "depends_on" (an array of ids this step needs first; [] if it needs nothing).
3. Put a step in depends_on ONLY when it truly needs that step's OUTPUT. Steps with [] run IN PARALLEL — maximize parallelism, minimize chains.
4. Write each "task" so it stands alone. Do NOT write "use the previous result"; say WHAT it needs (e.g. "Using the research findings provided to you, write..."). The dependent step will be GIVEN the prior outputs at runtime.
5. ids must be unique. depends_on may only reference ids that exist earlier in the array. No cycles.

Return EXACTLY this shape:
{"steps":[{"id":"s1","agent":"research","task":"...","depends_on":[]},{"id":"s2","agent":"software","task":"...","depends_on":["s1"]}]}

EXAMPLE — User: "Research the top 3 note-taking apps, then write me a markdown comparison and save it to notes.md":
{"steps":[{"id":"s1","agent":"research","task":"Search the web for the top 3 note-taking apps in 2026 and gather features, pricing, pros/cons.","depends_on":[]},{"id":"s2","agent":"software","task":"Using the research findings provided to you, write a markdown comparison table of the 3 apps and save it to notes.md via write_text_file.","depends_on":["s1"]}]}"""

AGGREGATION_PROMPT = """You are JARVIS giving the FINAL reply to the user after your departments did the work. Full persona: sharp-tongued, foul-mouthed, funny, butler-ish best-friend energy; you swear naturally, roast when deserved, always on his side. Default to ENGLISH; reply in Hindi (Devanagari) ONLY if the user's original message was in Hindi.

You are given the user's ORIGINAL request and the RESULTS of each step. Fuse them into ONE clean, useful answer, as if you did it all yourself. Output ONLY the reply text (no JSON, no step ids, no "Step/agent" labels, no meta-talk about a plan).

- Lead with the actual payoff — the answer/result he wanted, not a play-by-play.
- Weave results into one voice; resolve overlaps; drop redundancy. If steps disagree, trust the more specific/sourced one.
- If a file was written, a message sent, an app opened, or a PC action taken, state plainly it's done (and the name/target). Don't claim something that a step reported as failed.
- If a step failed or returned nothing, own it briefly and honestly — never invent results, facts, links, or numbers.
- If the work produced code or SQL, include it cleanly in a code block and say how/where to run it.
- Keep the persona but stay genuinely useful and tight. Match the user's language."""

# Heuristic: which messages are worth the planning detour. Bias HARD toward simple.
# Single words are matched on word boundaries (so "reanalyze"/"india vs australia"
# don't trip it); genuine multi-step phrases are matched as substrings.
_COMPLEX_WORDS = re.compile(r"\b(research|compare|summari[sz]e|analy[sz]e)\b", re.IGNORECASE)
_COMPLEX_PHRASES = (
    "and then", "then write", "then save", "then create", "then open", "after that",
    "afterwards", "step by step", "and save", "and write", "and create",
    "and summarize", "and analyze", "and email", "and message", "and build", "; then",
)

# Spoken-language → reply-language directive (voice mode passes a detected language).
_LANG_NAMES = {"en": "English", "hi": "Hindi (Devanagari script)", "kn": "Kannada (Kannada script)"}


def _lang_directive(lang):
    name = _LANG_NAMES.get(lang)
    if not name:
        return ""
    # Goes in the USER turn (most-obeyed position) to override the persona's English default.
    return (f"(Write your ENTIRE reply in {name} — ignore your default-language habit, "
            f"and don't say you can't, you can.)")


def _apply_lang(text, lang):
    d = _lang_directive(lang)
    return f"{d}\n\n{text}" if d else text


class Orchestrator:
    def __init__(self):
        self.general = make_agent("general")  # persistent → keeps conversational memory
        self.workers = getattr(config, "ORCH_MAX_WORKERS", 3)
        self.last_plan = None  # the most recent task graph, for inspection/dashboard
        self.memory = MemoryManager() if getattr(config, "MEMORY_ENABLED", True) else None

    # ── logging ────────────────────────────────────────────────────────────────
    def _log(self, line):
        if getattr(config, "ORCHESTRATOR_VERBOSE", True):
            print(f"[orchestrator] {line}", file=sys.stderr)

    # ── entry point ─────────────────────────────────────────────────────────────
    def handle(self, user_text: str, lang: str = None) -> str:
        """Handle a turn. `lang` (e.g. 'hi','kn' from voice STT) forces the reply language."""
        recall = self.memory.recall_context(user_text) if self.memory else ""
        reply = self._respond(user_text, recall, lang)
        if self.memory:
            self.memory.capture_async(user_text, reply)  # learn from this turn, in background
        return reply

    def _respond(self, user_text: str, recall: str, lang: str = None) -> str:
        eff = _apply_lang(user_text, lang)  # reply-language directive rides in the user turn
        if not self._looks_complex(user_text):
            self.general.set_memory_context(recall)
            return self.general.run(eff)  # fast path: everyday assistant

        self._log("complex request → planning…")
        steps = self._plan(user_text)
        if not steps:
            self._log("planning failed → handling as a single general request")
            self.general.set_memory_context(recall)
            return self.general.run(eff)

        if len(steps) == 1:
            s = steps[0]
            self._log(f"single step → {s['agent']}")
            if s["agent"] == "general":
                self.general.set_memory_context(recall)
                return self.general.run(eff)  # keep conversational memory + persona
            # Route the lone specialist result through aggregation so the reply gets
            # the full persona and the deterministic language handling.
            agent = make_agent(s["agent"])
            agent.set_memory_context(recall)
            result = agent.run(s["task"])
            return self._aggregate(user_text, [(s["id"], s["agent"], result)], recall, lang)

        depts = ", ".join(sorted({s["agent"] for s in steps}))
        self._log(f"running {len(steps)} steps across {depts}")
        results = self._execute(steps, recall)
        self._log("aggregating results…")
        return self._aggregate(user_text, results, recall, lang)

    # ── 1. classify (heuristic) ─────────────────────────────────────────────────
    def _looks_complex(self, text: str) -> bool:
        if len(text.split()) < 7:
            return False  # short asks are almost always one step
        low = text.lower()
        return bool(_COMPLEX_WORDS.search(low)) or any(p in low for p in _COMPLEX_PHRASES)

    # ── 2. plan ──────────────────────────────────────────────────────────────────
    def _plan(self, user_text: str):
        for attempt in range(2):
            nudge = "" if attempt == 0 else "\n\nReturn ONLY valid JSON in the required shape."
            msg = chat(
                [{"role": "system", "content": PLAN_PROMPT + nudge},
                 {"role": "user", "content": user_text}],
                options={"temperature": 0.1},
                route="planning",  # reasoning/planning gets its own Gemini key
            )
            try:
                steps = self._parse_plan(msg.get("content") or "")
            except Exception:
                steps = None  # any malformed plan → retry once, then fall back
            if steps:
                self.last_plan = steps
                return steps
        return None

    def _parse_plan(self, text):
        data = extract_json(text)
        if not isinstance(data, dict):
            return None
        steps = data.get("steps")
        if not isinstance(steps, list) or not steps or len(steps) > 8:
            return None
        valid_agents = set(DEPARTMENTS) | {"general"}
        seen = set()
        for s in steps:
            if not isinstance(s, dict):
                return None
            sid, agent, task, deps = s.get("id"), s.get("agent"), s.get("task"), s.get("depends_on", [])
            if not (isinstance(sid, str) and sid and sid not in seen):
                return None
            if agent not in valid_agents or not isinstance(task, str) or not task:
                return None
            if (not isinstance(deps, list)
                    or any(not isinstance(d, str) for d in deps)  # guard unhashable deps
                    or any(d not in seen for d in deps)):
                return None  # deps must reference an EARLIER step (no forward refs / cycles)
            seen.add(sid)
            s["depends_on"] = deps
        return steps

    # ── 3. execute (parallel waves over the dependency graph) ────────────────────
    def _execute(self, steps, recall=""):
        by_id = {s["id"]: s for s in steps}
        done = {}
        pending = {s["id"] for s in steps}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as ex:
            while pending:
                ready = [sid for sid in pending
                         if all(d in done for d in by_id[sid]["depends_on"])]
                if not ready:  # should not happen post-validation; fail safe
                    for sid in pending:
                        done[sid] = "(step skipped: unresolved dependencies)"
                    break
                futures = {ex.submit(self._run_step, by_id[sid], done, recall): sid for sid in ready}
                for fut in concurrent.futures.as_completed(futures):
                    sid = futures[fut]
                    try:
                        done[sid] = fut.result()
                    except Exception as e:
                        done[sid] = f"(step failed: {e})"
                    self._log(f"{sid} ({by_id[sid]['agent']}) done")
                    pending.discard(sid)
        # Return in the planner's original order for a stable aggregation prompt.
        return [(s["id"], s["agent"], done.get(s["id"], "")) for s in steps]

    def _run_step(self, step, done, recall=""):
        self._log(f"{step['id']} ({step['agent']}) running…")
        deps = step["depends_on"]
        if deps:
            context = "\n".join(f"[{d}]: {done.get(d, '')}" for d in deps)
            task = (f"Context from earlier steps:\n{context}\n\nYour task: {step['task']}")
        else:
            task = step["task"]
        agent = make_agent(step["agent"])
        agent.set_memory_context(recall)  # let specialists use what's known about the user
        return agent.run(task)

    # ── 4. aggregate ─────────────────────────────────────────────────────────────
    def _aggregate(self, user_text, results, recall="", lang=None):
        block = "\n\n".join(f"[{sid} - {agent}]:\n{text}" for sid, agent, text in results)
        # Decide the reply language deterministically — small models don't reliably
        # obey a conditional rule. A voice-detected `lang` wins; else detect by script.
        directive = _lang_directive(lang)
        if not directive:
            hindi = bool(re.search(r"[ऀ-ॿ]", user_text))
            directive = ("Reply in Hindi, Devanagari script." if hindi
                         else "Reply in ENGLISH only, no Hindi.")
        system = AGGREGATION_PROMPT + f"\n\nIMPORTANT: {directive}"
        if recall:
            system += "\n\n" + recall
        msg = chat(
            [{"role": "system", "content": system},
             {"role": "user",
              "content": f"User's original request:\n{user_text}\n\nResults from each step:\n{block}\n\n{directive}\nWrite the final reply."}],
            options={"temperature": config.TEMPERATURE},
            route="planning",  # reasoning/synthesis gets its own Gemini key
        )
        return (msg.get("content") or "").strip()

    def reset(self):
        self.general.reset()

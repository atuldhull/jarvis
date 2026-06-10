"""JARVIS — the assistant loop (text-first).

Phase 1 gave it a voice in text. Phase 2 gives it hands: it can now call tools
(tell the time, open an app, open a website, search the web) whenever your request
needs a real action — and Phase 3 adds full browser control.

Run it:
    .venv\\Scripts\\activate          (once per terminal, to use the project's venv)
    py main.py
Type to chat. Say 'exit', 'quit', or 'bye' — or press Ctrl+C — to leave.
"""

import sys

import config

# Windows terminals default to cp1252, which crashes on the em-dashes / smart quotes
# JARVIS naturally produces. Force UTF-8 so replies never blow up mid-sentence.
sys.stdout.reconfigure(encoding="utf-8")


def main():
    # The orchestrator delegates complex jobs to specialist departments and runs
    # them in parallel; everyday messages take its fast single-agent path. Set
    # config.ORCHESTRATOR_ENABLED = False to use the plain single agent instead.
    if getattr(config, "ORCHESTRATOR_ENABLED", True):
        from agents.orchestrator import Orchestrator
        jarvis = Orchestrator()
        respond = jarvis.handle
    else:
        from brain.agent import Agent
        jarvis = Agent()
        respond = jarvis.run
    print(f"JARVIS online — brain: {config.MODEL}. (type 'exit' to leave)\n")

    while True:
        try:
            user_text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nJARVIS: Until next time, sir.")
            break

        if not user_text:
            continue
        if user_text.lower() in {"exit", "quit", "bye"}:
            print("JARVIS: Very good, sir. Powering down.")
            break

        try:
            reply = respond(user_text)
        except Exception as e:
            # Most common cause: Ollama server not running, or the model in
            # config.py isn't pulled. The message says which.
            print(f"JARVIS: I hit a snag, sir — {e}\n")
            continue

        print(f"JARVIS: {reply}\n")


if __name__ == "__main__":
    main()

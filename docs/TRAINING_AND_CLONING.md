# JARVIS — Training, Datasets & Cloning (Minute-Format Guide)

> **Training reference.** Exactly what to train, from where to get every dataset,
> what to clone and how — step by step, in fine detail, all verified 2026-06-07 (see
> [VERIFIED_FINDINGS.md](VERIFIED_FINDINGS.md)). Tuned for your **RTX 4050 6 GB / Ryzen 7
> 8845HS / 16 GB / Windows 11 / Python 3.13**. Total required spend: **₹0.**

---

## 0. TL;DR — the one-screen answer

- **Do you NEED to train?** No. Build the working assistant first (system prompt + tools).
  Persona is ~80% solved by a system prompt with **zero training**.
- **Can you train the real brain (`qwen3.5:4b`) on your laptop?** **No** — it needs ~10 GB
  VRAM (bf16 LoRA) and the 4-bit shortcut is banned for Qwen3.5. **Train it free on Colab**,
  then download + run it on your 6 GB card.
- **What CAN you train on the laptop?** A ~3B model (e.g. **Llama-3.2-3B QLoRA ≈ 3.5 GB**) —
  good for *learning the workflow*.
- **What do you "clone"?** A **voice** (zero-shot, not training) with **Chatterbox Turbo**
  (MIT), or just use the ready British voice **Kokoro `bm_george`**.
- **What you NEVER train:** an LLM from scratch, the wake word (pre-made), STT/TTS (download).

```
TRAIN (optional, later):  Qwen3.5-4B  --bf16 LoRA-->  FREE COLAB T4 (16GB)  -->  GGUF  -->  ollama create jarvis
LEARN-AT-HOME (optional):  Llama-3.2-3B  --QLoRA 3.5GB-->  YOUR 4050 (6GB)    -->  GGUF  -->  ollama create
CLONE (inference, anytime): ~10s voice clip  -->  Chatterbox Turbo (MIT, 6GB-fit)  -->  custom JARVIS voice
```

---

## 1. The three meanings of "train" (so they're never confused)

| Meaning | Your laptop? | Reality |
|---|---|---|
| **Train an LLM from scratch** | ❌ impossible | Needs thousands of GPUs + millions of $. No laptop on Earth does this, and it'd be *worse* than free models. |
| **Fine-tune** (LoRA/QLoRA — nudge an existing model) | ✅ small models | The only "training" you'd ever do. Bakes in persona + sharper tool-calling. |
| **Clone a voice** | ✅ (it's inference) | Zero-shot — no training at all, just a ~10s reference clip. |

---

## 2. WHAT to fine-tune, and WHERE (the hard hardware truth)

**Running ≠ training.** These are different VRAM problems:

| Model | RUN (Ollama) | FINE-TUNE | Where to fine-tune |
|---|---|---|---|
| **Qwen3.5-4B** (the brain) | 3.4 GB ✅ your laptop | **~10 GB** (bf16 LoRA; QLoRA banned) ❌ laptop | **Free Colab T4 (16 GB)** |
| Qwen3.5-2B | 2.7 GB ✅ | ~5 GB (tight, may OOM on Windows) 🧪 | laptop *barely*, or Colab |
| **Llama-3.2-3B** | 2 GB ✅ | **~3.5 GB (QLoRA)** ✅ laptop | **Your 4050** (learn here) |

> 🔴 Verified verbatim from Unsloth: *"It is not recommended to do QLoRA (4-bit) training on
> the Qwen3.5 models … due to higher than normal quantization differences."* And the bf16
> LoRA table lists **4B = 10 GB**. That is why the 4B is a Colab-only training job.

**Decision rule:**
- Want the *best* result that runs on your laptop → **fine-tune Qwen3.5-4B on free Colab.**
- Want to *learn fine-tuning on your own machine* → **QLoRA Llama-3.2-3B locally** (accept its
  Llama Community License — fine for personal use, not "fully free").

**The toolchain = [Unsloth](https://unsloth.ai)** (fastest, ~70–80% less VRAM, free Colab
notebooks, and it **auto-exports a GGUF + an Ollama Modelfile with the exact chat template**
baked in — a template mismatch is the #1 cause of gibberish output). No-code alternative:
**LLaMA-Factory** (`llamafactory-cli webui`).

---

## 3. The datasets — from where, exactly (all verified)

### 3.1 The shortlist (start here)

| Dataset | HuggingFace ID | License | Why |
|---|---|---|---|
| ⭐ ToolACE | `Team-ACE/ToolACE` | Apache-2.0 | 11.3k rows, tiny, highest quality-per-row; trains fast on free Colab |
| ⭐ Glaive (ShareGPT) | `hiyouga/glaive-function-calling-v2-sharegpt` | Apache-2.0 | 100k rows, **already clean role format** — use this, not the raw glaive |
| Hermes FC | `NousResearch/hermes-function-calling-v1` | Apache-2.0 | ~9.7k, adds JSON-mode / structured output |
| xLAM (optional) | `Salesforce/xlam-function-calling-60k` | CC-BY-4.0 | 60k strict JSON tool calls — ⚠️ **gated** (accept terms) + needs format conversion |
| ToolMind (later) | `Nanbeige/ToolMind` | Apache-2.0* | 368k / ~4 GB — overkill for a first run; *re-bundles* CC-BY-NC data |
| APIGen-MT (personal) | `Salesforce/APIGen-MT-5k` | CC-BY-**NC** | 5k multi-turn — fine for **personal** JARVIS only |

> ⚠️ Avoid the raw `glaiveai/glaive-function-calling-v2` for training — it stores everything
> as two big strings you'd have to parse. The `hiyouga/...-sharegpt` version is pre-split.

### 3.2 The persona dataset — YOU write this (~100–300 rows)

This is what turns "a competent tool-caller" into **JARVIS specifically**. Every row carries
the **same** butler system prompt. Format (ShareGPT JSONL, one object per line):

```json
{"system":"You are JARVIS, a calm, dry-witted British butler. Address the user as 'sir'. Be concise, deferential, a touch wry. Never break character.","conversations":[{"from":"human","value":"what's the weather like"},{"from":"gpt","value":"A touch grey over the city this morning, sir — 18 degrees and threatening rain. Shall I set out the umbrella reminder?"}]}
```

Cover: greetings, polite refusals, confirming-before-irreversible-actions **in character**,
small talk, and **~30% rows that ALSO emit a tool call** so the butler voice survives
function-calling. Speed it up: have your local `qwen2.5:7b`/`gemma2:9b` rewrite ~30 neutral
Q&As "in the voice of a dry British butler who calls the user sir," then **hand-edit every
one** (never ship raw generations).

> 💡 You can skip fine-tuning entirely at first and just put this butler system prompt in
> the runtime — that alone gets ~80% of the JARVIS voice, free, instantly.

### 3.3 The mix ratio

~**60%** glaive-sharegpt (subsample to ~15k) + **~25%** ToolACE (all 11.3k) + **~15%** your
persona (~150–300). Persona is small *on purpose* — too much hurts tool-calling.

---

## 4. Fine-tuning, step by step

### 4.1 Path A — the REAL brain on FREE Colab (recommended)

1. **Build the data on your laptop** (it's just text). In Python:
   ```python
   from datasets import load_dataset
   ta = load_dataset("Team-ACE/ToolACE")
   gl = load_dataset("hiyouga/glaive-function-calling-v2-sharegpt")
   ```
   Write your `persona.jsonl` (§3.2). For xLAM, first visit its HF page **logged in** and
   click *"Agree and access"* (it's gated).
2. **Open a free Colab notebook:** github.com/unslothai/notebooks → a **Qwen3.5 / Qwen3 (4B)
   conversational** notebook → *Runtime → Change runtime type → T4 GPU*.
3. **Load in bf16 (NOT 4-bit):**
   ```python
   from unsloth import FastLanguageModel
   model, tok = FastLanguageModel.from_pretrained(
       "unsloth/Qwen3.5-4B", max_seq_length=4096, load_in_4bit=False)  # QLoRA forbidden here
   model = FastLanguageModel.get_peft_model(model, r=16, lora_alpha=16,
       use_gradient_checkpointing="unsloth")
   ```
4. **Train** with `SFTTrainer`: `per_device_train_batch_size=1–2`,
   `gradient_accumulation_steps=4–8`, `learning_rate=2e-4`, a few hundred steps, 1–3 epochs.
   ~10 GB fits the T4's 16 GB. Free T4 = ~12 h sessions, ~15–30 GPU-hrs/week.
5. **Export GGUF + Modelfile (same notebook):**
   ```python
   model.save_pretrained_gguf("jarvis", tok, quantization_method="q4_k_m")
   ```
   Download `jarvis-*.gguf` **and** the auto-written `Modelfile`.
6. **Import on your laptop:** put both in one folder, point the Modelfile's `FROM` line at the
   local `.gguf`, then:
   ```powershell
   ollama create jarvis -f Modelfile
   ollama run jarvis
   ```
7. **Sanity-check immediately:** 5 tool-calling prompts (valid JSON calls?) + 5 persona prompts
   (stays in butler voice?). 🔴 If output is gibberish in Ollama but was fine in Colab → it's a
   chat-template/EOS mismatch: re-export with Unsloth's **auto** Modelfile (never hand-write
   one). Past Unsloth Qwen3-class GGUF bugs exist — if broken, update Unsloth/llama.cpp & re-export.

### 4.2 Path B — learn on YOUR laptop (Llama-3.2-3B QLoRA)

1. **One-time install** (Windows native, no WSL for plain QLoRA): NVIDIA driver + CUDA Toolkit
   + **Visual Studio Build Tools (C++ workload)**, then:
   ```powershell
   py -m pip install torch --index-url https://download.pytorch.org/whl/cu124
   py -m pip install unsloth
   ```
   *(If this install fights you — common for beginners — just use Colab Path A instead.)*
2. **Train (fits 6 GB):**
   ```python
   from unsloth import FastLanguageModel
   model, tok = FastLanguageModel.from_pretrained(
       "unsloth/Llama-3.2-3B-Instruct-bnb-4bit", max_seq_length=1024, load_in_4bit=True)
   model = FastLanguageModel.get_peft_model(model, r=16, lora_alpha=16,
       use_gradient_checkpointing="unsloth")
   # SFTTrainer(... per_device_train_batch_size=1, gradient_accumulation_steps=4, max_steps=60)
   ```
   OOM? Drop `max_seq_length` to 512, keep batch size 1.
3. **Export + import** exactly like Path A steps 5–7.

---

## 5. Voice CLONING — what & how (this is inference, not training)

### 5.1 The easy route (no cloning): Kokoro `bm_george`

Calm British male, Apache-2.0, **runs real-time on CPU → 0 VRAM** (the GPU stays 100% for the
brain). Set `lang_code='b'` (British) — `'a'` is American.
```powershell
py -m pip install kokoro soundfile
# install espeak-ng: download the .msi from github.com/espeak-ng/espeak-ng/releases, run it, restart terminal
```
```python
from kokoro import KPipeline; import soundfile as sf
pipe = KPipeline(lang_code='b')
gen = pipe("Good evening, sir. All systems are online.", voice='bm_george')
audio = next(iter(gen))[2]; sf.write("jarvis.wav", audio, 24000)
```

### 5.2 The cloning route (custom voice): Chatterbox Turbo (MIT, fits 6 GB)

Zero-shot clone from a **~10-second** clean WAV (mono, no music).
```powershell
py -m pip install chatterbox-tts
```
```python
from chatterbox.tts import ChatterboxTTS; import torchaudio as ta
m = ChatterboxTTS.from_pretrained(device='cuda')   # use 'cpu' if you hit CUDA OOM (0 VRAM, slower)
wav = m.generate("Welcome home, sir.", audio_prompt_path="ref.wav")
ta.save("clone.wav", wav, m.sr)
```
**6 GB tips (verified):** use the **Turbo (350M)** model, *not* the 500M original (which wants
8 GB+). For the smoothest no-code path use the **`BetaDoggo/Chatterbox-tts-low-vram`** fork
(Gradio UI, set chunk size ≤500). 🔴 *Do not* set `TTS_BF16=on` against the plain pip package —
that flag lives in the separate **devnen/Chatterbox-TTS-Server**. Best architecture: **clone
once, cache the WAVs, reuse** → cloning becomes a one-time VRAM cost.

> ⚖️ **Legal line:** cloning **your own** voice or a consenting friend's / royalty-free audio
> = fine. Cloning a real person's or the actual movie-JARVIS voice = **private, non-distributed
> use only**. Every Chatterbox output carries an inaudible "Perth" watermark by design.

### 5.3 Optional: fine-tune STT on YOUR voice (later, free)

Record ~30–60 min of your speech + transcripts → HF "Fine-Tune Whisper" or
`Vaibhavs10/fast-whisper-finetuning` PEFT notebook on **free Colab T4** (<8 GB) → ~500 steps
(~45 min) → merge LoRA → `ct2-transformers-converter --quantization int8` → load locally in
faster-whisper. Do this **only after** the whole voice loop already works.

---

## 6. What you do NOT train (settle it once)

| Component | Train it? | Do this instead |
|---|---|---|
| Wake word "Hey Jarvis" | ❌ | openWakeWord ships a **pre-made** `hey_jarvis` model |
| STT (ears) | ❌ (optional later) | Download faster-whisper + a Whisper model |
| TTS (voice) | ❌ | Download Kokoro/Piper; clone = zero-shot |
| The LLM from scratch | ❌ never | Download Qwen3.5; optionally LoRA-fine-tune it |

---

## 7. Cost & honest expectations

- **Cost:** ₹0. Free models, free datasets, free Colab.
- **Reality check:** fine-tuning is **optional polish**, not a prerequisite, and the real brain
  can't be trained on your laptop (use Colab). A local 4B is capable but **not GPT-class** — set
  expectations accordingly and lean on the system-prompt persona first.

**Order of operations:** build text brain → tool-calling → Playwright agent (Phases 1–3 in
[BUILD_GUIDE_MINUTE.md](BUILD_GUIDE_MINUTE.md)) **first**. Only then come back here to fine-tune.

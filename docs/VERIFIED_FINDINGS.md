# JARVIS — Verified Findings (Fact-Check Ledger)

> **Date: 2026-06-07.** Every claim below was checked against live primary sources
> (official Ollama tag pages, Hugging Face model/dataset cards, GitHub repos, and official
> docs), then double-checked by trying to *refute* it before trusting it. This file is the
> ground truth the other build docs rely on.
>
> Confidence tags below: ✅ = confirmed on a primary source · ⚠️ = correct but with a
> caveat · 🔴 = a correction to the older docs · 🧪 = needs an empirical test on *your*
> machine before you fully depend on it.

---

## 1. Brain (LLM, inference) — ✅ HIGH

| Claim | Verdict | Source |
|---|---|---|
| `qwen3.5:4b` is real: 3.4 GB disk, Q4_K_M, 4.66B params, Apache-2.0, 256K ctx, native tool-calling | ✅ confirmed | ollama.com/library/qwen3.5:4b + HF Qwen/Qwen3.5-4B |
| 🔴 `qwen3.5:4b` is **MULTIMODAL** (vision+text), not text-only as first assumed | ✅ confirmed | HF card ("Unified Vision-Language Foundation"); Ollama badge "vision tools thinking" |
| `qwen3:4b` is the leaner **text-only** equivalent (2.5 GB) | ✅ confirmed | ollama.com/library/qwen3 |
| `qwen3:8b` is the "push-it" pick (5.2 GB) — fits but **tight**, KV spills to RAM | ✅ confirmed | ollama.com/library/qwen3:8b |
| `qwen2.5:7b` (already installed) is Apache-2.0, solid baseline | ✅ confirmed | ollama.com/library/qwen2.5:7b |
| `qwen3.6` has **no** 6 GB-fitting size (smallest = 27B / ~17 GB) | ✅ confirmed | ollama.com/library/qwen3.6/tags |
| `llama3.1:8b` fits (4.9 GB) but is **Llama Community License**, not Apache | ✅ confirmed | ollama.com/library/llama3.1:8b |
| 🔴 Ollama **defaults to only 4K context** on any GPU < 24 GiB VRAM | ✅ confirmed | docs.ollama.com/context-length |
| There was a Qwen3.5 tool-call parsing bug fixed ~Mar 2026; on 0.24.0 update to current stable | ⚠️ confirmed (exact fixed version string is muddled — update to current stable & test) | github.com/ollama/ollama/issues/14745 |

**Action:** primary brain = `qwen3.5:4b`; lean/fast alt = `qwen3:4b`; quality ceiling =
`qwen3:8b`; day-one baseline = your existing `qwen2.5:7b`. Raise context deliberately.

---

## 2. Fine-tuning the brain — ✅ HIGH (this is the most important correction)

| Claim | Verdict | Source |
|---|---|---|
| 🔴 You **cannot** fine-tune `qwen3.5:4b` on the 6 GB laptop | ✅ confirmed | Unsloth Qwen3.5 docs |
| Unsloth **forbids 4-bit QLoRA on Qwen3.5** ("higher than normal quantization differences") | ✅ confirmed (verbatim) | unsloth.ai/docs/models/qwen3.5/fine-tune |
| Qwen3.5 **bf16 LoRA** VRAM: 0.8B=3GB, 2B=5GB, **4B=10GB**, 9B=22GB | ✅ confirmed (verbatim table) | same |
| Free Colab T4 = **16 GB**, ~12h sessions, ~15–30 GPU-hrs/week → fits the 4B (10 GB) | ✅ confirmed | 2026 Colab specs |
| Laptop **can** QLoRA a ~3B model (Llama-3.2-3B ≈ 3.5 GB) — QLoRA allowed (rule is Qwen3.5-specific) | ✅ confirmed | Unsloth requirements table |
| QLoRA "minimums" (3B=3.5GB, 7B=5GB, 8B=6GB) are Linux/batch-1 **floors**; Windows steals VRAM | ⚠️ honest reframe | Unsloth requirements |
| Llama-3.2-3B is **Llama Community License** (700M-MAU cap, EU restriction), not Apache | ⚠️ confirmed | HF unsloth/Llama-3.2-3B-Instruct-bnb-4bit |
| Unsloth installs **natively on Windows** for LoRA/QLoRA (needs PyTorch+CUDA+VS C++ Build Tools) | ✅ confirmed | unsloth.ai Windows install |

**Action:** real brain fine-tune → **free Colab**; local learning run → **Llama-3.2-3B
QLoRA**. Dependable local ceiling = ~3B. Never promise an 8B local fine-tune on Windows.

---

## 3. Datasets — ✅ HIGH

| Dataset | Rows | License | Verdict |
|---|---|---|---|
| Team-ACE/ToolACE | 11,300 / 37 MB | Apache-2.0 | ✅ primary, cleanest |
| hiyouga/glaive-function-calling-v2-sharegpt | 100,563 / 251 MB | Apache-2.0 | ✅ use this (clean ShareGPT) |
| glaiveai/glaive-function-calling-v2 (raw) | 112,960 / 271 MB | Apache-2.0 | ✅ exists; awkward 2-string format |
| NousResearch/hermes-function-calling-v1 | ~9.7k (5 configs) | Apache-2.0 | ✅ smaller than docs imply |
| Salesforce/xlam-function-calling-60k | 60,000 | CC-BY-4.0 | ⚠️ gated + attribution + format-convert |
| Nanbeige/ToolMind | 368,611 / ~4 GB | Apache-2.0* | ⚠️ re-bundles NC data; overkill first run |
| Salesforce/APIGen-MT-5k | 5,000 | CC-BY-**NC** | ⚠️ personal use only |

Format facts (verified): **LLaMA-Factory** = ShareGPT (roles `human/gpt/function_call/observation`
+ `system`/`tools`, registered in `dataset_info.json`). **Unsloth** = ChatML / `conversations`
+ `apply_chat_template`. *(low-confidence numeric drift: glaive raw 112,960 vs sharegpt 100,563.)*

---

## 4. STT (ears) for Indian-English / Hinglish — ✅ HIGH

| Claim | Verdict | Source |
|---|---|---|
| `faster-whisper` (CTranslate2) is the engine — MIT, v1.2.1, ~4× faster, int8 ~1.5 GB VRAM | ✅ confirmed | github.com/SYSTRAN/faster-whisper |
| Start pick `deepdml/faster-whisper-large-v3-turbo-ct2` (MIT, ready CT2, multilingual) | ✅ confirmed | HF card |
| 🔴 Oriserve Prime/Swift are fine-tuned from **large-v3** (NOT turbo); **Apex** IS turbo-based, 0.8B | ✅ confirmed | HF Oriserve cards |
| Oriserve models output **romanized Latin Hinglish** ("mera naam…") — ideal for an LLM; Apache-2.0 | ✅ confirmed | HF cards |
| Srota `moorlee/qwen3-asr-0.6b-hinglish` real but 15.85% WER is **in-domain**, no CT2 path → defer | ✅ confirmed | HF Forums |
| 🔴 On Python 3.13 use **`webrtcvad-wheels`** (cp313 wheel), NOT plain `webrtcvad`; `sounddevice` 0.5.5 fine | ✅ confirmed | PyPI |
| You **can** LoRA-fine-tune Whisper on your own voice free on Colab T4 (<8 GB) | ✅ confirmed | HF PEFT / Whisper disc #988 |

---

## 5. TTS + voice cloning — ✅ HIGH (2 precision fixes)

| Claim | Verdict | Source |
|---|---|---|
| Kokoro-82M `bm_george` = British male, grade "C", Apache-2.0, **CPU real-time → 0 VRAM**; lang_code `'b'` | ✅ confirmed | HF hexgrad/Kokoro-82M + VOICES.md |
| Chatterbox / **Turbo (350M)** = genuinely **MIT**, zero-shot clone via `audio_prompt_path`, Perth watermark | ✅ confirmed | github.com/resemble-ai/chatterbox |
| Standard 500M wants ~8 GB+ → on 6 GB use **Turbo** + low-vram fork (`BetaDoggo/Chatterbox-tts-low-vram`, chunk ≤500) or CPU | ✅ confirmed | HF ResembleAI/chatterbox-turbo |
| 🔴 `TTS_BF16=on` belongs to the **devnen server**, NOT base `chatterbox-tts` — don't set it against plain pip | ⚠️ corrected | github.com/devnen/Chatterbox-TTS-Server |
| 🔴 Piper `en_GB-alan-medium` license is **genuinely unconfirmed** (not confirmed CC-BY-SA) → personal use only | ⚠️ corrected | HF rhasspy MODEL_CARD |
| Avoid: F5-TTS (CC-BY-NC), XTTS-v2 (CPML + Coqui defunct), IndexTTS-2 (~8–12 GB, NC) | ✅ confirmed | respective cards |

**Cloning is zero-shot INFERENCE, not training.** TTS *fine-tuning* → free Colab, later.

---

## 6. Wake word — ✅ HIGH

| Claim | Verdict | Source |
|---|---|---|
| openWakeWord ships a pre-trained `hey_jarvis` (200k synth clips + ~31k h negatives), ONNX, CPU-only | ✅ confirmed | github.com/dscripka/openWakeWord |
| 🔴 Code is Apache-2.0 but the **pretrained models are CC-BY-NC-SA-4.0** (non-commercial) | ✅ confirmed | HF davidscripka/openwakeword |
| Works on Windows + Python 3.13 (onnxruntime 1.26.0 has cp313 wheel); the 3.13 breakage is Linux-only | ✅ confirmed (the "tflite-runtime Linux-only" *reasoning* was imprecise; conclusion holds) | PyPI onnxruntime |
| Picovoice Porcupine free tier **disabled after June 30 2026**, no free replacement → avoid | ✅ confirmed | HA community thread |
| livekit-wakeword (Apache-2.0, v0.2.1 May 2026) = optional later accuracy upgrade, training-only for "hey jarvis" | ✅ confirmed | github.com/livekit/livekit-wakeword |

---

## 7. Computer & browser control — ✅ HIGH

| Claim | Verdict | Source |
|---|---|---|
| Playwright Python v1.60.0, Apache-2.0, **0 VRAM**; persistent-context login pattern is real | ✅ confirmed | pypi.org/project/playwright |
| 🔴 Chrome **blocks automating its default profile** → use a separate empty `user_data_dir` (verbatim in docs) | ✅ confirmed | playwright.dev BrowserType |
| 🔴 `browser-use` (MIT, v0.12.9) **is unreliable with small local models** — its own docs warn smaller Qwen emit bad action schemas | ✅ confirmed | docs.browser-use.com/supported-models |
| 🔴 pywinauto (BSD-3, v0.6.9) needs **`comtypes>=1.4.8`** on Python 3.13 or it crashes (`CUIAutomation`) | ✅ confirmed | PyPI comtypes 1.4.16 |
| Alt: `uiautomation` (yinkaisheng) v2.0.29, Apache-2.0, more recent | ✅ confirmed | PyPI |
| 🔴 **UIPI**: a non-elevated script can't automate an app running as Administrator | ✅ confirmed | Microsoft Learn |
| Stagehand v3 dropped Playwright / TS-first → skip; Skyvern AGPL/Docker → niche only | ✅ confirmed | Browserbase blog; Skyvern repo |

**Recommended architecture (key finding):** hand-written Playwright "tool" functions the
4B LLM *selects by name*, **not** full-autonomous browser-use.

---

## 8. Optional vision / GUI grounding — ✅ HIGH

| Claim | Verdict | Source |
|---|---|---|
| 🔴 The brain `qwen3.5:4b` **is itself a vision model** → grounds screenshots with **zero extra VRAM / no swap** | ✅ confirmed | ollama.com/library/qwen3.5 |
| Holo2-4B (Apache-2.0, from Qwen3-VL-4B-Thinking) = best dedicated grounder; GGUF Q4_K_M 2.7 GB **+ required mmproj 0.6 GB** | ✅ confirmed | HF Hcompany/Holo2-4B + mradermacher GGUF |
| 🔴 Moondream 2 = 1.8B, **1.7 GB** (docs' 0.9 GB is stale), Apache-2.0 | ✅ confirmed | ollama.com/library/moondream |
| Moondream 3 (~9B MoE, ~19 GB) does **not** fit 6 GB | ✅ confirmed | HF moondream3-preview |
| On 6 GB you **cannot** hold a separate VLM + the brain at once → swap (or reuse the multimodal brain) | ✅ confirmed | arithmetic vs verified sizes |

---

## 9. Cross-cutting risks & things to test on YOUR machine (🧪)

1. 🧪 **Concurrent VRAM:** does brain + whisper-int8 actually co-fit on GPU at usable context? Watch `ollama ps`; if a big CPU share shows, lower `OLLAMA_CONTEXT_LENGTH`.
2. 🧪 **Real context headroom** for the *multimodal* `qwen3.5:4b` (vision encoder eats some) — the "8K–16K" figure was for text-only `qwen3:4b`.
3. 🧪 **Tool-calling in practice:** can the 4B chain multi-step Playwright actions without derailing? Measure with real tasks.
4. 🧪 **GGUF export:** past Unsloth Qwen3-class GGUF bugs ("GGGG" output) — sanity-check the model in Ollama immediately after import.
5. ⚠️ **Expectation:** a local 4B is capable but not GPT-class; it will stall on anti-bot/CAPTCHA/2FA and novel open-ended tasks. Build retries + a human confirm step.
6. ⚠️ **Safety surface:** stored logins + a persistent logged-in browser = irreversible-action risk. The confirm-before-irreversible guardrail is **not optional**.

See [TRAINING_AND_CLONING.md](TRAINING_AND_CLONING.md) and
[BUILD_GUIDE_MINUTE.md](BUILD_GUIDE_MINUTE.md) for the step-by-step build.

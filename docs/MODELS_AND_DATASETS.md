# JARVIS — Models, Datasets & Where to Get Everything

⭐ **The core document.** Every model, exact source, size, whether you train it, and the
datasets — all with links and costs.

Tuned for: **RTX 4050 Laptop (6 GB VRAM), Ryzen 7 8845HS, 16 GB RAM.**
**Last refreshed: 2026-06-03** (checked against live sources). ⚠️ = updated since
late-2025. Sizes are approximate — verify with `ollama show` / model cards.

---

## 0. The golden rule (read first)

> **You download pre-trained models. You do not train an LLM from scratch.**
> Everything below is **free** unless explicitly marked optional. "Training" only ever
> appears in three optional places: (1) a wake word — already pre-made for "Hey Jarvis";
> (2) voice cloning — *zero-shot*, no real training; (3) fine-tuning the brain — optional,
> free on Google Colab. **Required training = none.**

---

## 1. THE BRAIN — the LLM

The intelligence: understands you, plans tasks, chooses tools.

### Train or download? → **DOWNLOAD. Free.** (Apache-2.0)

### How to get it
- Install **Ollama**: <https://ollama.com> → `ollama pull qwen3.5:4b`
- ⚠️ **Use a current Ollama build** (a Qwen3.5 tool-call parsing bug was fixed ~Mar 2026).

### Which model for YOUR 6 GB GPU

| Model | Pull command | Size (disk) | Fits 6GB? | Tool-calling | Notes |
|---|---|---|---|---|---|
| **Qwen3.5 4B** ⭐ | `ollama pull qwen3.5:4b` | ~3.4 GB | ✅ Comfortably | ⭐⭐⭐ Excellent (native) | **Best pick.** Thinking/fast modes, Apache-2.0 |
| Qwen3.5 2B | `ollama pull qwen3.5:2b` | ~2.7 GB | ✅ Easily, fastest | ⭐⭐⭐ Very good | Use for max speed / simple tool sets |
| Qwen3 8B | `ollama pull qwen3:8b` | ~5.2 GB | ✅ Tight | ⭐⭐⭐ Excellent | More reasoning; keep context small |
| Llama 3.1 8B | `ollama pull llama3.1:8b` | ~4.9 GB | ✅ Yes | ⭐⭐ Good | Fast, strong English; restricted license |

> ⚠️ **This replaces the late-2025 Qwen2.5 7B recommendation.** The Qwen3.x **4B** class
> now does tool-calling *better* than the old 7B while using *less* VRAM — so you go
> **smaller and better** at once. Qwen3.6 exists but has no small dense variant that fits
> 6 GB, so Qwen3.5 4B is the sweet spot.

**Practical notes for 6 GB:** weights are ~2.5 GB in VRAM; keep context to a few-K to
low-tens-of-K tokens for snappy voice latency (the 256 K max won't fit on 6 GB). Use the
**non-thinking/fast mode** for quick voice turns, enable **thinking** only for hard
multi-step plans.

### Cost: **₹0.**

---

## 2. THE EARS — Speech-to-Text (STT)

Turns mic audio → text.

### Train or download? → **DOWNLOAD. Free.**

### Engine: **faster-whisper** (`pip install faster-whisper`)
- GitHub: <https://github.com/SYSTRAN/faster-whisper> — most mature local/streaming stack.

### Two-tier pick (you have an Indian accent / may speak Hinglish)

| Use case | Model | How to get | Size | Notes |
|---|---|---|---|---|
| **General, low-latency** ⭐ | whisper-large-v3-turbo (int8) | checkpoint `deepdml/faster-whisper-large-v3-turbo-ct2` | ~1.5 GB VRAM | Multilingual, ~25–30× real-time |
| **Best Indian-English / Hinglish** ⭐ | Oriserve **Whisper-Hindi2Hinglish-Apex** | <https://huggingface.co/Oriserve/Whisper-Hindi2Hinglish-Apex> | 0.8 B | Apache-2.0; outputs romanized Hinglish; convert to CTranslate2 int8 |
| **Newest dedicated Hinglish** | **Srota** (`moorlee/qwen3-asr-0.6b-hinglish`) | <https://huggingface.co/moorlee/qwen3-asr-0.6b-hinglish> | ~780 M | 15.85% WER; mixed Devanagari+Latin. ≤30 s chunks, no CT2 path yet |

> ⚠️ **Note:** Apex is a fine-tune of large-v3-**turbo** (not
> large-v3). Generic `small`/`distil-large-v3` are now superseded by turbo (same speed,
> multilingual). **Parakeet / Canary** top English leaderboards but have **no Hindi** — not
> usable for Hinglish despite the headline numbers.

**Mic + VAD libraries:** `pip install sounddevice webrtcvad`. Stick to int8 on the 4050.

### Cost: **₹0.**

---

## 3. THE VOICE — Text-to-Speech (TTS)

Full deep-dive in **[VOICE.md](VOICE.md)** — summary here.

### Train or download? → **DOWNLOAD. Free.** (Cloning = zero-shot, no training.)

| Engine | Quality | Where | British? | Notes |
|---|---|---|---|---|
| **Kokoro-82M** ⭐ | Excellent | <https://huggingface.co/hexgrad/Kokoro-82M> | ✅ `bm_george` | Apache-2.0, ~300 MB, real-time on CPU |
| **Piper** | Good | <https://github.com/rhasspy/piper> | ✅ `en_GB-alan-medium` | Lightest CPU fallback. ⚠️ *alan* voice ~CC-BY-SA (personal use ok) |
| **Chatterbox** (clone) | Excellent + clones | <https://github.com/resemble-ai/chatterbox> | clone any | **MIT**, zero-shot from ~5–10 s. ⚠️ use **Turbo/low-VRAM** build on 6 GB |
| F5-TTS / XTTS-v2 (clone) | Highest fidelity | HF | clone any | ⚠️ **non-commercial** licenses; personal use only |

> ⚠️ **Note:** the standard Chatterbox 500 M model wants ~8–16 GB — on your 6 GB
> card use the **Turbo (350 M)** model and/or a low-VRAM fork (chunking), or CPU. Kokoro's
> British male voices are graded "C/D+" (good, not flawless). For premium custom voices,
> cloning is the route — see [VOICE.md](VOICE.md).

### Cost: **₹0.**

---

## 4. THE WAKE WORD — "Hey Jarvis"

### Train or download? → **DOWNLOAD a pre-made one. Free.**

### Pick — **openWakeWord** (ships a pre-trained `hey_jarvis` model!)
- GitHub: <https://github.com/dscripka/openWakeWord> · `pip install openwakeword`
- `from openwakeword.model import Model; oww = Model(wakeword_models=["hey_jarvis"])`
- Free, Apache-2.0, CPU-only, fully offline. The model auto-downloads on first run.
- Accuracy upgrade reusing the SAME model: **livekit-wakeword** (Feb 2026, Apache-2.0,
  backward-compatible) — <https://github.com/livekit/livekit-wakeword>

> ⚠️ **AVOID Picovoice Porcupine for the free path.** Picovoice is **discontinuing its
> free tier on June 30, 2026** — existing free AccessKeys get disabled. It had a built-in
> "Jarvis" keyword, but its free route is ending. openWakeWord stays free forever.

**Custom wake word (optional):** openWakeWord trains one from **synthetic speech** on a
free **Google Colab** notebook (~10 min–1 hr). You won't need it — "hey_jarvis" is ready.

### Cost: **₹0.**

---

## 5. COMPUTER CONTROL — libraries, not models

How JARVIS *acts*. No models/datasets/training — free Python libraries.

| Capability | Library | Install |
|---|---|---|
| **Browser automation** ⭐ | Playwright | `pip install playwright` → `playwright install` |
| **Autonomous browsing** | browser-use (MIT) | `pip install browser-use` |
| Open apps / files / shell | `subprocess`, `os` | built-in |
| Windows app control | pywinauto (primary) | `pip install pywinauto` |
| Mouse/keyboard fallback | PyAutoGUI | `pip install pyautogui` |
| OCR (read screen text) | pytesseract | `pip install pytesseract` + Tesseract |
| Credential storage | keyring | `pip install keyring` |

> ⚠️ **Playwright login tip:** use `launch_persistent_context(user_data_dir=...)` with a
> **separate, empty** profile folder (NOT Chrome's default profile — recent Chrome blocks
> automating it). Log in once interactively; cookies persist across runs.
> **Reliability:** DOM-driven (Playwright/browser-use) beats pure vision clicking — make it
> your default; reserve vision for canvas/anti-bot UIs.

### Cost: **₹0.**

---

## 6. (OPTIONAL, ADVANCED) Vision — "look at the screen and click"

Only for Level-4 control (no API, no clean HTML). Needs a small vision model on 6 GB.

| Model | Size | Get it | Notes |
|---|---|---|---|
| **Holo2-4B** ⭐ | ~2–3 GB | H Company (Nov 2025, Qwen3-VL) | Current GUI-grounding SOTA at this size |
| Moondream 2 (1.8B) | ~0.9 GB | `ollama pull moondream` | Lightest; trivially fits |
| UI-TARS-1.5-7B | ~4.6 GB (Q4) | `Mungert/UI-TARS-1.5-7B-GGUF` | Tight on 6 GB |

> ⚠️ Holo**1.5** is outdated (Holo2/Holo3 superseded it). Moondream **3** Preview (~19 GB)
> does NOT fit. Pull GGUFs from a community repo (e.g. mradermacher), not the original
> safetensors-only repo. You usually **can't** hold a vision model + a big LLM in 6 GB at
> once — keep the VLM for grounding only. **Skip this entirely until much later.**

---

## 7. (OPTIONAL, ADVANCED) Fine-tuning the brain — datasets live here

You almost certainly **don't need this.** Pre-trained model + good system prompt + tools
already behaves like JARVIS. Only fine-tune to bake in a custom persona / squeeze
reliability.

### How (free)
- **Unsloth** — free Colab notebooks: <https://github.com/unslothai/unsloth>
  (also LLaMA-Factory no-code UI, Axolotl, TRL).
- Train on **free Colab T4 (15 GB)**, not your 6 GB laptop. Run the result locally.
- ⚠️ **Do not do 4-bit QLoRA on Qwen3.5** (Unsloth: quantization error too high) — use
  **bf16 LoRA** for Qwen3.5, or pick **Llama-3.2-3B** / **FunctionGemma-270M** for a QLoRA
  path.

### Free datasets (Hugging Face)

| Purpose | Dataset | License | Link |
|---|---|---|---|
| Tool/function calling | Glaive Function Calling v2 (113k) | Apache-2.0 | <https://huggingface.co/datasets/glaiveai/glaive-function-calling-v2> |
| Verified tool calls | Salesforce xLAM-60k | CC-BY-4.0 | <https://huggingface.co/datasets/Salesforce/xlam-function-calling-60k> |
| Mixed FC + JSON mode | NousResearch hermes-function-calling-v1 | Apache-2.0 | <https://huggingface.co/datasets/NousResearch/hermes-function-calling-v1> |
| Diverse/complex tools | Team-ACE ToolACE | Apache-2.0 | <https://huggingface.co/datasets/Team-ACE/ToolACE> |
| Reasoning multi-turn (360k) | Nanbeige ToolMind (Nov 2025) | Apache-2.0 | <https://huggingface.co/datasets/Nanbeige/ToolMind> |
| Multi-turn trajectories | Salesforce APIGen-MT-5k | ⚠️ CC-BY-**NC** | <https://huggingface.co/datasets/Salesforce/APIGen-MT-5k> |

> ⚠️ **No "₹100 per dataset" spend is needed** — these are **free**. License note:
> FunctionGemma is under Gemma terms, Llama 3.2 under a restricted community license — not
> "fully free." For a personal assistant that's all fine.

### Cost: **₹0** (free Colab). Optional Colab Pro ≈ ₹1000/mo — not required.

---

## 8. Your recommended download list

Total disk ≈ **10–14 GB** (you have ~371 GB free). All free.

```
1. Ollama                          → ollama pull qwen3.5:4b      (~3.4 GB)
2. pip install faster-whisper      → turbo-int8 checkpoint       (~1.5 GB)
3. Kokoro-82M (bm_george) OR Piper → from HF                     (~0.3 GB)
4. pip install openwakeword        → bundled 'hey_jarvis' model  (~0.05 GB)
5. pip install playwright          → playwright install          (~0.4 GB)
6. pip install browser-use pywinauto pyautogui keyring sounddevice webrtcvad
```

Everything: **₹0, zero models trained from scratch, fits your machine.**

---

## 9. VRAM budget — how 6 GB is shared (important)

| Component | Where it runs | VRAM |
|---|---|---|
| Brain (Qwen3.5 4B) | **GPU** | ~2.5–4 GB (w/ context) |
| STT (whisper turbo int8) | GPU or CPU | ~1.5 GB (or 0 on CPU) |
| TTS (Kokoro/Piper) | **CPU** | ~0 |
| Wake word (openWakeWord) | **CPU** | ~0 |

✅ **Recommended:** brain on GPU, **TTS + wake word on CPU**, STT on GPU (fits — the 4B
leaves room) or CPU. This stays responsive on 6 GB with headroom to spare — a big benefit
of dropping from a 7B to the 4B brain.

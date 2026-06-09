# JARVIS — Voice In Depth (Ears + Voice)

Everything about hearing you and talking back — including a free British "JARVIS" voice
and voice cloning. All free. **Refreshed & fact-checked: 2026-06-03.** ⚠️ = updated.

---

## Part A — THE EARS (Speech-to-Text / STT)

### Tool: faster-whisper (free, local)
- `pip install faster-whisper` · <https://github.com/SYSTRAN/faster-whisper>
- The most mature local + streaming STT stack. Models auto-download from Hugging Face.

### Because you have an Indian accent / may speak Hinglish — a two-tier choice

1. **General + low-latency (start here):** **whisper-large-v3-turbo** in int8.
   - Checkpoint: `deepdml/faster-whisper-large-v3-turbo-ct2` (~1.5 GB VRAM, multilingual,
     ~25–30× real-time).
2. **Best accuracy on Indian-English / Hinglish:** **Oriserve Whisper-Hindi2Hinglish-Apex**
   - <https://huggingface.co/Oriserve/Whisper-Hindi2Hinglish-Apex> · 0.8 B · Apache-2.0
   - ⚠️ It's a fine-tune of large-v3-**turbo** (not large-v3). Outputs **romanized**
     (Latin-script) Hinglish, e.g. *"Haan vahi dekh aapko bataen na."*
   - Convert to CTranslate2 int8 (`ct2-transformers-converter ... --quantization
     int8_float16`) so it runs inside faster-whisper with streaming.
3. **Newest dedicated Hinglish (max accuracy, more setup):** **Srota**
   - `moorlee/qwen3-asr-0.6b-hinglish` · 15.85% WER conversational · mixed
     Devanagari+Latin output (*"मेरा favourite festival Diwali है"*). Caveat: ≤30 s
     chunks, vLLM-only streaming, no CTranslate2 path — an accuracy pick, not low-latency.

> ⚠️ **Skip these despite great headlines:** NVIDIA **Parakeet** and **Canary** top the
> English leaderboards but support **no Hindi/Hinglish**. `distil-large-v3` is now
> redundant vs turbo (same speed, but English-only).

### Model size guide (generic whisper, if you don't use a Hinglish tune)

| Model | Size | Notes |
|---|---|---|
| `base` | ~145 MB | Fast, short commands |
| `small` | ~480 MB | Decent balance |
| `large-v3-turbo` (int8) ⭐ | ~1.5 GB VRAM | Best speed/accuracy, multilingual |

### Supporting libs
- Mic capture: `pip install sounddevice` (or `pyaudio`)
- "Stopped talking" detection: `pip install webrtcvad`

### Cost: ₹0.

---

## Part B — THE VOICE (Text-to-Speech / TTS)

Three free routes — pick by taste.

### Route 1 — Kokoro-82M ⭐ (best ready-made British male, premium quality)
- Model: <https://huggingface.co/hexgrad/Kokoro-82M> · `pip install kokoro`
- Voice grades: <https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md>
- **British butler vibe:** voice **`bm_george`** (calm British male, ~138 Hz, ~165 WPM).
  ⚠️ Graded "C" (`bm_lewis` "D+") — good, not flawless, but the best free ready-made option.
- Apache-2.0, ~300 MB, **real-time on CPU** (leaves your GPU for the brain). Topped the
  TTS Arena in Jan 2026.

### Route 2 — Piper (lightest CPU fallback, fully offline)
- GitHub: <https://github.com/rhasspy/piper> · `pip install piper-tts`
- Voices: <https://huggingface.co/rhasspy/piper-voices> · samples:
  <https://rhasspy.github.io/piper-samples/>
- British picks: `en_GB-alan-medium`, `en_GB-northern_english_male-medium`,
  `en_GB-cori-high`.
- ⚠️ **License nuance:** the Piper *engine* is MIT, but the `en_GB-alan` *voice* is likely
  **CC-BY-SA** (it's Alan Pope's voice; the card is uncertain). **Fine for a personal
  JARVIS**, not for a commercial product.

### Route 3 — Voice CLONING (a custom JARVIS voice)
- **Chatterbox (Resemble AI) ⭐ — cleanest license:** **MIT**, zero-shot clone from
  ~5–10 s of reference audio.
  - Repo: <https://github.com/resemble-ai/chatterbox> · `pip install chatterbox-tts`
  - Windows self-host + Web UI: <https://github.com/devnen/Chatterbox-TTS-Server>
  - ⚠️ **6 GB caveat:** the standard 500 M model wants ~8–16 GB VRAM. On your 4050 use the
    **Turbo (350 M)** model and/or a **low-VRAM fork** (chunking), or run on CPU.
  - Beat ElevenLabs ~64% in a (vendor-run) blind test. Embeds an inaudible watermark.
- **F5-TTS** — highest cloning fidelity, but **CC-BY-NC** (non-commercial): personal use
  only. <https://huggingface.co/SWivid/F5-TTS> (`pip install f5-tts`). Apache-2.0 base
  `mrfakename/OpenF5-TTS-Base` exists but is alpha quality.
- **XTTS-v2 (Coqui)** — mature, clones from ~6 s, but **CPML non-commercial** and Coqui is
  shut down (license enforceability debated). Fine for personal hobby use.
- ⚠️ **IndexTTS-2** needs ~8 GB — too tight for 6 GB.

---

## Part C — Getting a "JARVIS voice" specifically

The movie JARVIS = calm, posh British male. Free ways:

1. **Easiest:** Kokoro `bm_george` (or a Piper `en_GB` voice). Done — no cloning.
2. **Cloning (Chatterbox Turbo):** feed a ~5–10 s clean reference clip of a voice you
   have the right to use, and it speaks in that voice.

### ⚖️ Legal/ethical note (read before cloning)
Cloning a real person's or a copyrighted movie voice is OK for **private, personal,
non-distributed** use — but do **not** publish or share audio of a cloned real/celebrity
voice; that can violate rights. Safest reference clips: **record yourself/a friend**, or
royalty-free audio you own the rights to (e.g. <https://freesound.org>, check licenses).

---

## Part D — Recommended voice setup for you

```
START:   whisper-large-v3-turbo int8 (ears)  +  Kokoro bm_george OR Piper en_GB-alan (voice, CPU)
         → fast, offline, leaves the GPU for the brain. ₹0.

HINGLISH: swap STT to Oriserve Whisper-Hindi2Hinglish-Apex (CTranslate2 int8)
         → much better on Indian-accented / mixed speech. ₹0.

CUSTOM:  Chatterbox Turbo voice clone for a unique JARVIS voice (GPU/CPU). ₹0.
```

### Optional paid voice (NOT needed)
**ElevenLabs** (<https://elevenlabs.io>) has the most lifelike voices (free tier ~10k
chars/mo; paid ≈ ₹420/mo). **Skip it** — Kokoro/Piper/Chatterbox are free and good.

### Cost of the whole voice stack: ₹0.

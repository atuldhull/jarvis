# JARVIS — Multilingual Voice (Sarvam)

JARVIS understands and speaks **English, Hindi, Kannada, Hinglish, and mixed**
conversations — and replies in the language you used, automatically.

```
you speak (any language)
   └─ STT detects the language ─┐
                                ▼
        brain replies in that same language (persona intact)
                                │
   speaks it back ◀─ TTS in the matching voice
```

Two layers make it work, and both **degrade gracefully**:

1. **Voice I/O — Sarvam (optional cloud).** When a Sarvam key is set, JARVIS uses Sarvam
   for speech-to-text (great Indian-language accuracy, auto-detects the language) and
   text-to-speech (natural Indian voices, including **Kannada** which the local voices
   can't do). No key / offline → it falls straight back to local **faster-whisper + Piper**.
2. **Reply language — the brain.** The detected language is passed to the orchestrator,
   which forces the reply into that language (overriding the default-English habit) while
   keeping JARVIS's persona. In practice: ask in any language, get Kannada/Hindi/English back.

---

## Setup

1. Get a free key at **https://dashboard.sarvam.ai**.
2. Add it to `keys.json`:
   ```json
   "sarvam": ["your-sarvam-key"]
   ```
   (or set env `SARVAM_KEY`). That's it — `voice_main.py` picks it up on launch.

Without a key, everything still runs on the **local** voice stack (English + Hindi via Piper;
Kannada needs Sarvam). Set `SARVAM_ENABLED = False` in `config.py` to force local always.

---

## Config ([config.py](../config.py))

| Setting | Meaning |
|---|---|
| `SARVAM_ENABLED` | use Sarvam when a key is present |
| `SARVAM_STT_MODEL` | Sarvam ASR model (`saarika:v2`) |
| `SARVAM_TTS_MODEL` / `SARVAM_TTS_SPEAKER` | Sarvam TTS model + voice |
| `SUPPORTED_LANGS` | languages to handle (`en`, `hi`, `kn`) |

---

## Status

- ✅ **Reply-language switching** — working (Kannada / Hindi / English, persona kept).
- ✅ **Graceful fallback** — no key → local faster-whisper + Piper; never breaks the voice loop.
- ✅ **Sarvam STT/TTS** — Hindi round-trip (synthesize → transcribe) works,
  language auto-detected. Models: TTS `bulbul:v2`, STT `saarika:v2.5`. Fixes the local
  Whisper-base bug where Hindi/Kannada came out as Arabic.

Voice mode (`py voice_main.py`) now runs on the **full orchestrator** — so voice gets memory,
the specialist departments, and multilingual replies, not just a bare chat loop.

---

## The pieces

```
voice/sarvam.py    Sarvam STT + TTS client (stdlib HTTP; None on any failure → local)
ears/stt.py        Sarvam-first transcription, lazy faster-whisper fallback, exposes last_lang
voice/tts.py       script-aware TTS: Sarvam → Piper → Windows voice
agents/orchestrator.py   forces the reply language from the detected/spoken language
```

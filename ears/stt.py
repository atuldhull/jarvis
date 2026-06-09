"""Ears — speech-to-text via faster-whisper (local, offline).

Loads once, then transcribes a wav file to text. The model auto-downloads on first
use. Swap config.STT_MODEL for the turbo or Oriserve Hinglish checkpoints later.
"""

import config


class STT:
    def __init__(self):
        # Imported here so the rest of JARVIS runs even before faster-whisper exists.
        from faster_whisper import WhisperModel

        self.model = WhisperModel(
            config.STT_MODEL, device=config.STT_DEVICE, compute_type="int8"
        )

    def transcribe(self, wav_path: str) -> str:
        segments, _ = self.model.transcribe(wav_path, language=config.STT_LANGUAGE)
        return " ".join(s.text for s in segments).strip()

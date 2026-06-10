"""Ears — speech-to-text. Sarvam (Indian languages) first, local faster-whisper fallback.

If a Sarvam key is set and the call works, we use it (better Hindi/Kannada/Hinglish and
it auto-detects the language). Otherwise we fall back to local faster-whisper, which is
loaded LAZILY — so if Sarvam handles everything, the Whisper model never even loads.
`last_lang` holds the detected 2-letter language of the most recent transcription.
"""

import config
from voice import sarvam


class STT:
    def __init__(self):
        self._model = None       # faster-whisper, loaded on first local use only
        self.last_lang = "en"

    def _local(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(
                config.STT_MODEL, device=config.STT_DEVICE, compute_type="int8")
        return self._model

    def transcribe(self, wav_path: str) -> str:
        if sarvam.available():
            res = sarvam.stt(wav_path)
            if res:
                text, lang = res
                self.last_lang = lang or "en"
                return text
        # Local fallback (offline / no Sarvam key / Sarvam errored).
        segments, info = self._local().transcribe(wav_path, language=config.STT_LANGUAGE)
        self.last_lang = getattr(info, "language", None) or "en"
        return " ".join(s.text for s in segments).strip()

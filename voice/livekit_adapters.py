"""LiveKit adapters — let LiveKit drive the conversation while JARVIS's own brain and
voice stay in charge.

LiveKit Agents gives us the "feels human" layer: VAD, turn-taking, interruptions/barge-in,
and streamed playback. But its default STT/LLM/TTS plugins are paid cloud services. These
three thin adapters plug OUR stack in instead:

  JarvisSTT  → our Sarvam/faster-whisper transcription (also reports the spoken language)
  JarvisLLM  → our full Orchestrator (memory + departments + task routing + multilingual)
  JarvisTTS  → our Sarvam/Piper voice

Built for livekit-agents 1.5.x.
"""

import asyncio
import io
import uuid
import wave

from livekit import rtc
from livekit.agents import APIConnectOptions, llm, stt, tts

import config
import voice.tts as tts_engine
from ears.stt import STT as LocalSTT


# ── STT: our transcription, with detected language ───────────────────────────
class JarvisSTT(stt.STT):
    def __init__(self):
        super().__init__(capabilities=stt.STTCapabilities(streaming=False, interim_results=False))
        self._engine = LocalSTT()       # Sarvam-first, faster-whisper fallback
        self.last_lang = "en"

    async def _recognize_impl(self, buffer, *, language=None, conn_options=None):
        frame = rtc.combine_audio_frames(buffer)
        with open("_lk_in.wav", "wb") as f:
            f.write(frame.to_wav_bytes())
        text = await asyncio.get_event_loop().run_in_executor(
            None, self._engine.transcribe, "_lk_in.wav")
        self.last_lang = self._engine.last_lang or "en"
        return stt.SpeechEvent(
            type=stt.SpeechEventType.FINAL_TRANSCRIPT,
            alternatives=[stt.SpeechData(language=self.last_lang, text=text or "")])


# ── LLM: our orchestrator (keeps memory, departments, routing, multilingual) ──
def _last_user_text(chat_ctx) -> str:
    items = getattr(chat_ctx, "items", None) or getattr(chat_ctx, "messages", [])
    for item in reversed(list(items)):
        if getattr(item, "role", None) == "user":
            tc = getattr(item, "text_content", None)
            if tc:
                return tc
            content = getattr(item, "content", None)
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return " ".join(c for c in content if isinstance(c, str))
    return ""


class JarvisLLMStream(llm.LLMStream):
    def __init__(self, llm_, *, chat_ctx, tools, conn_options, orch, lang):
        super().__init__(llm_, chat_ctx=chat_ctx, tools=tools, conn_options=conn_options)
        self._orch = orch
        self._lang = lang

    async def _run(self):
        text = _last_user_text(self._chat_ctx)
        if not text:
            return
        # Orchestrator is blocking (network + tools) → run off the event loop.
        reply = await asyncio.get_event_loop().run_in_executor(
            None, self._orch.handle, text, self._lang)
        self._event_ch.send_nowait(llm.ChatChunk(
            id=str(uuid.uuid4()),
            delta=llm.ChoiceDelta(role="assistant", content=reply or "")))


class JarvisLLM(llm.LLM):
    def __init__(self, orchestrator, stt_ref):
        super().__init__()
        self._orch = orchestrator
        self._stt = stt_ref  # to read the language detected for this utterance

    def chat(self, *, chat_ctx, tools=None, conn_options=None, **kwargs):
        return JarvisLLMStream(
            self, chat_ctx=chat_ctx, tools=tools or [],
            conn_options=conn_options or APIConnectOptions(),
            orch=self._orch, lang=getattr(self._stt, "last_lang", "en"))


# ── TTS: our voice (Sarvam/Piper) ────────────────────────────────────────────
class JarvisTTSStream(tts.ChunkedStream):
    async def _run(self, output_emitter):
        wav_bytes = await asyncio.get_event_loop().run_in_executor(
            None, tts_engine.synth_bytes, self._input_text)
        if not wav_bytes:
            return
        with wave.open(io.BytesIO(wav_bytes), "rb") as w:
            sr, ch = w.getframerate(), w.getnchannels()
            pcm = w.readframes(w.getnframes())
        output_emitter.initialize(
            request_id=str(uuid.uuid4()), sample_rate=sr, num_channels=ch, mime_type="audio/pcm")
        output_emitter.push(pcm)
        output_emitter.flush()


class JarvisTTS(tts.TTS):
    def __init__(self):
        super().__init__(capabilities=tts.TTSCapabilities(streaming=False),
                         sample_rate=22050, num_channels=1)

    def synthesize(self, text, *, conn_options=None):
        return JarvisTTSStream(tts=self, input_text=text,
                               conn_options=conn_options or APIConnectOptions())

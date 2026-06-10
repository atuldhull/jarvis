"""JARVIS — voice mode (Phase 4/5): wake → listen → think → speak.

Needs a microphone + speakers and the voice libs installed. Loads the STT and
wake-word models on start (the first run downloads them). The brain and tools are
exactly the same as text mode — voice is just the wrapper.

Run:  py voice_main.py
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")

import config
from agents.orchestrator import Orchestrator
from ears.mic import record_to_wav
from ears.stt import STT
from ears.wakeword import WakeWord
from voice.tts import say


def main():
    print("Loading voice stack (first run downloads models)...")
    wake = WakeWord()
    stt = STT()
    jarvis = Orchestrator()  # full brain: memory + departments + task routing
    print(f"Ready. Say 'Hey Jarvis' to wake me (brain: {config.MODEL}).")

    while True:
        wake.wait()
        print("listening...")
        text = stt.transcribe(record_to_wav())
        print("you:", text)
        if not text:
            continue
        if text.lower().strip(" .") in {"exit", "quit", "stop", "goodbye", "good bye"}:
            say("Until next time, sir.")
            break
        try:
            reply = jarvis.handle(text, lang=stt.last_lang)  # reply in the spoken language
        except Exception as e:
            print("JARVIS: (error)", e)
            say("My apologies, sir — I had trouble just then. Please try again.")
            continue
        print("JARVIS:", reply)
        say(reply)


if __name__ == "__main__":
    main()

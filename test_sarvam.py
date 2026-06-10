"""Sarvam multilingual tests: script detection, language directives, graceful fallback."""

import sys

sys.stdout.reconfigure(encoding="utf-8")

import config
config.ROUTER_VERBOSE = False
config.ORCHESTRATOR_VERBOSE = False

from voice import sarvam
from voice.tts import _lang_of
from agents.orchestrator import _lang_directive, _apply_lang, Orchestrator


def test_script_detection():
    assert _lang_of("Hello there, boss") == "en"
    assert _lang_of("नमस्ते दोस्त, क्या हाल है") == "hi"
    assert _lang_of("ನಮಸ್ಕಾರ ಗೆಳೆಯ") == "kn"
    print("1) script detection: English→en, Devanagari→hi, Kannada→kn")


def test_lang_directive():
    assert "Kannada" in _lang_directive("kn") and "Hindi" in _lang_directive("hi")
    assert "English" in _lang_directive("en")
    assert _lang_directive(None) == "" and _lang_directive("xx") == ""
    print("2) language directive: maps en/hi/kn, blank for none/unknown")


def test_graceful_fallback():
    if sarvam.available():
        print("3) Sarvam key DETECTED — ready to verify the live API")
    else:
        assert sarvam.stt("does_not_exist.wav") is None
        assert sarvam.tts("hello", "en") is None
        print("3) no Sarvam key → stt/tts return None → local faster-whisper/Piper used")


def test_apply_lang():
    wrapped = _apply_lang("say hello", "kn")
    assert "Kannada" in wrapped and wrapped.endswith("say hello")
    assert _apply_lang("say hello", None) == "say hello"  # no wrap when no language
    print("4) language directive is prepended to the user turn (or left untouched)")


if __name__ == "__main__":
    test_script_detection()
    test_lang_directive()
    test_graceful_fallback()
    test_apply_lang()
    print("\n✅ multilingual (Sarvam) tests passed")

"""Microphone capture with voice-activity detection (VAD).

Records from the moment you start speaking until you actually stop (a short pause),
instead of a fixed window — so it never cuts you off mid-sentence. A hard time cap
keeps it from listening forever.
"""

import config


def record_to_wav(path: str = "_input.wav") -> str:
    import numpy as np
    import sounddevice as sd
    import soundfile as sf
    import webrtcvad

    sr = config.SAMPLE_RATE
    frame_ms = 30
    frame_len = int(sr * frame_ms / 1000)              # 480 samples @ 16 kHz = a valid VAD frame
    silence_limit = config.SILENCE_MS // frame_ms       # silent frames that end your turn
    max_frames = int(config.MAX_RECORD_SECONDS * 1000 / frame_ms)

    vad = webrtcvad.Vad(config.VAD_AGGRESSIVENESS)
    frames = []
    silent = 0
    started = False

    with sd.InputStream(samplerate=sr, channels=1, dtype="int16", blocksize=frame_len) as stream:
        for _ in range(max_frames):
            block, _ = stream.read(frame_len)
            is_speech = vad.is_speech(block[:, 0].tobytes(), sr)
            if is_speech:
                started, silent = True, 0
                frames.append(block.copy())
            elif started:
                silent += 1
                frames.append(block.copy())          # keep trailing silence so words aren't clipped
                if silent >= silence_limit:
                    break
            # before you've started talking, ignore the leading silence

    audio = np.concatenate(frames) if frames else np.zeros((1, 1), dtype="int16")
    sf.write(path, audio, sr)
    return path

"""Wake word — 'Hey Jarvis' via openWakeWord (CPU, offline, no GPU).

openWakeWord ships a pretrained 'hey_jarvis' model, so nothing is trained here.
It runs on the CPU in a few MB of RAM, leaving the GPU entirely for the brain.
"""

import config


class WakeWord:
    def __init__(self):
        import openwakeword
        from openwakeword.model import Model

        openwakeword.utils.download_models()  # one-time fetch of hey_jarvis + feature models
        self.model = Model(wakeword_models=[config.WAKEWORD])

    def wait(self):
        """Block until 'Hey Jarvis' is heard, then return."""
        import numpy as np
        import sounddevice as sd

        with sd.InputStream(samplerate=config.SAMPLE_RATE, channels=1, dtype="int16") as stream:
            while True:
                audio, _ = stream.read(1280)  # 80 ms frames at 16 kHz
                scores = self.model.predict(np.asarray(audio).flatten())
                if scores.get(config.WAKEWORD, 0) > config.WAKEWORD_THRESHOLD:
                    self.model.reset()
                    return

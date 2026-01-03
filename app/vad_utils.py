import webrtcvad

class VADDetector:
    def __init__(self, aggressiveness: int = 2):
        """
        aggressiveness: 0–3 (3 = most sensitive to silence)
        """
        self.vad = webrtcvad.Vad(aggressiveness)

    def is_speech(self, frame: bytes, sample_rate: int = 16000) -> bool:
        """
        frame must be 20, 30 or 10 ms of audio.
        """
        return self.vad.is_speech(frame, sample_rate)

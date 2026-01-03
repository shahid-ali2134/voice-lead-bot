from faster_whisper import WhisperModel
from config import WHISPER_MODEL_SIZE, WHISPER_DEVICE, INPUT_AUDIO_FILE
from logger import get_logger

logger = get_logger(__name__)

class WhisperService:
    def __init__(self, model_size: str = WHISPER_MODEL_SIZE, device: str = WHISPER_DEVICE):
        """
        Initialize Whisper model on the chosen device.
        """
        try:
            logger.info(f"🎤 Loading Whisper model: {model_size} on {device}")
            self.model = WhisperModel(model_size, device=device)
            logger.info("✅ Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load Whisper model: {e}")
            raise

    def transcribe(self, audio_file: str = INPUT_AUDIO_FILE) -> str:
        """
        Transcribe the given audio file and return the transcribed text.
        """
        try:
            logger.info(f"🎧 Transcribing audio file: {audio_file}")
            segments, info = self.model.transcribe(audio_file)
            transcription = " ".join([seg.text for seg in segments])
            logger.info(f"📝 Transcription complete (lang: {info.language}): {transcription}")
            return transcription
        except Exception as e:
            logger.error(f"❌ Whisper transcription failed: {e}")
            raise

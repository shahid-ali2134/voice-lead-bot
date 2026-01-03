import os
import io
import soundfile as sf
from TTS.api import TTS
from config import TTS_MODEL_NAME, TTS_OUTPUT_FILE
from logger import get_logger

logger = get_logger(__name__)

class TTSService:
    def __init__(self, model_name: str = TTS_MODEL_NAME):
        """
        Initialize the TTS model (Glow-TTS).
        """
        logger.info(f"🔊 Initializing TTS model: {model_name}")
        try:
            self.tts = TTS(model_name=model_name, progress_bar=False, gpu=True)
            logger.info("✅ TTS model loaded successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to load TTS model: {e}")
            raise

    def synthesize(self, text: str, output_file: str = TTS_OUTPUT_FILE) -> str:
        """
        Generate audio from text and save to file.
        """
        try:
            logger.info(f"📝 Generating speech for text: {text}")
            self.tts.tts_to_file(text=text, file_path=output_file)
            logger.info(f"✅ Audio generated at: {os.path.abspath(output_file)}")
            return output_file
        except Exception as e:
            logger.error(f"❌ TTS synthesis failed: {e}")
            raise

    def synthesize_to_memory(self, text: str):
        """
        Convert text to speech and return as BytesIO (WAV format),
        so playback can happen without writing to disk.
        """
        try:
            # Write to temp wav file
            temp_path = TTS_OUTPUT_FILE
            self.tts.tts_to_file(text=text, file_path=temp_path)

            # Read the file into memory
            data, samplerate = sf.read(temp_path)
            buffer = io.BytesIO()
            sf.write(buffer, data, samplerate, format='WAV')
            buffer.seek(0)
            return buffer
        except Exception as e:
            logger.error(f"❌ TTS in-memory synthesis failed: {e}")
            raise

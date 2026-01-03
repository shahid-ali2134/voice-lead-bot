import os
import io
import simpleaudio as sa
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from pydub import AudioSegment
from logger import get_logger

logger = get_logger(__name__)

# ====================== CONFIG ======================
load_dotenv()

ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVEN_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "Xb7hH8MSUJpSbSDYk0k2")
ELEVEN_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")

# Playback settings
TARGET_SAMPLE_RATE = 22050
TARGET_CHANNELS = 1

class TTSService:
    def __init__(self):
        """
        Initialize ElevenLabs TTS client.
        """
        logger.info(f"🔊 Initializing ElevenLabs TTS voice: {ELEVEN_VOICE_ID}")
        try:
            self.client = ElevenLabs(api_key=ELEVEN_API_KEY)
            logger.info("✅ ElevenLabs TTS initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ElevenLabs TTS: {e}")
            raise

    def synthesize_to_memory(self, text: str):
        """
        Convert text to speech using ElevenLabs and return as BytesIO WAV.
        Downsamples to match the pipeline's target playback settings.
        """
        try:
            logger.info(f"📝 Generating speech for text: {text}")

            # Stream MP3 audio from ElevenLabs
            response = self.client.text_to_speech.convert(
                voice_id=ELEVEN_VOICE_ID,
                model_id=ELEVEN_MODEL_ID,
                text=text,
                voice_settings={
                    "stability": 0.5,
                    "similarity_boost": 0.7
                }
            )

            # Combine response chunks
            mp3_data = b"".join(response)

            # Convert MP3 to WAV and downsample
            audio_segment = AudioSegment.from_file(io.BytesIO(mp3_data), format="mp3")
            audio_segment = audio_segment.set_frame_rate(TARGET_SAMPLE_RATE).set_channels(TARGET_CHANNELS)

            # Optional slight slowdown for more natural pacing
            audio_segment = audio_segment._spawn(audio_segment.raw_data, overrides={
                "frame_rate": int(audio_segment.frame_rate * 0.95)
            }).set_frame_rate(TARGET_SAMPLE_RATE)

            wav_buffer = io.BytesIO()
            audio_segment.export(wav_buffer, format="wav")
            wav_buffer.seek(0)

            logger.info("✅ Speech synthesis completed in-memory.")
            return wav_buffer
        except Exception as e:
            logger.error(f"❌ ElevenLabs TTS synthesis failed: {e}")
            raise

    def play(self, audio_buffer: io.BytesIO):
        """
        Play audio directly from in-memory buffer.
        """
        try:
            wave_obj = sa.WaveObject(audio_buffer.read(), num_channels=TARGET_CHANNELS, bytes_per_sample=2, sample_rate=TARGET_SAMPLE_RATE)
            play_obj = wave_obj.play()
            play_obj.wait_done()
        except Exception as e:
            logger.error(f"❌ Playback failed: {e}")
            raise

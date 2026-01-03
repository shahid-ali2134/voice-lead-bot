import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 🧠 LLM (Ollama) Configuration
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# 🎤 Whisper Configuration
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")  # small | medium | large
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cuda")  # cuda | cpu

# 🗣️ TTS Configuration (Coqui TTS or any installed engine)
TTS_MODEL_NAME = os.getenv("TTS_MODEL_NAME", "tts_models/en/ljspeech/tacotron2-DDC")
TTS_OUTPUT_FILE = os.getenv("TTS_OUTPUT_FILE", "output.wav")

# 🎧 Audio / Voice Settings
INPUT_AUDIO_FILE = os.getenv("INPUT_AUDIO_FILE", "test_audio.wav")
OUTPUT_AUDIO_FILE = os.getenv("OUTPUT_AUDIO_FILE", "response.wav")
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "22050"))

# 🧰 System Settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # DEBUG | INFO | WARNING | ERROR
TEMP_DIR = os.getenv("TEMP_DIR", "./temp")

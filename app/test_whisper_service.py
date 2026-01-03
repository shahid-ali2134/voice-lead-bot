# test_whisper_service.py
from services.whisper_service import WhisperService

whisper = WhisperService()
text = whisper.transcribe("test_audio.wav")  # or leave empty to use default from config
print("📝 Transcribed Text:", text)

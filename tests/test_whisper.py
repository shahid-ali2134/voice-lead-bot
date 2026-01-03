from faster_whisper import WhisperModel

model = WhisperModel("small", device="cuda")
segments, info = model.transcribe("test_audio.wav")

print(f"🗣️ Detected language: {info.language}")
print("📜 Transcription:")
for segment in segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")

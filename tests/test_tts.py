from TTS.api import TTS

# Load English model
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=False)

print("🔊 Generating speech...")
tts.tts_to_file(
    text="Hello, this is your voice lead qualification bot speaking!",
    file_path="tts_output.wav"
)

print("✅ TTS test complete — check 'tts_output.wav'")

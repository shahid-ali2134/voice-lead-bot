import os
import io
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
import simpleaudio as sa
from pydub import AudioSegment

# ====================== CONFIG ======================
load_dotenv()
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "Xb7hH8MSUJpSbSDYk0k2"
MODEL = "eleven_multilingual_v2"

# Target playback config
TARGET_SAMPLE_RATE = 22050
TARGET_CHANNELS = 1

# ====================== CLIENT ======================
client = ElevenLabs(api_key=ELEVEN_API_KEY)

# ====================== TTS FUNCTION ======================
def synthesize_speech(text: str) -> bytes:
    """
    Generate speech from ElevenLabs, downsample to 22kHz mono.
    """
    response = client.text_to_speech.convert(
        voice_id=VOICE_ID,
        model_id=MODEL,
        text=text,
        voice_settings={
            "stability": 0.5,        # Balanced natural voice
            "similarity_boost": 0.7
        }
    )

    mp3_data = b"".join(response)
    audio_segment = AudioSegment.from_file(io.BytesIO(mp3_data), format="mp3")

    # 🪄 Convert to mono 22.05 kHz to match your pipeline
    audio_segment = audio_segment.set_frame_rate(TARGET_SAMPLE_RATE).set_channels(TARGET_CHANNELS)

    # 🐢 Optional slight slowdown (0.95x speed)
    audio_segment = audio_segment._spawn(audio_segment.raw_data, overrides={
        "frame_rate": int(audio_segment.frame_rate * 0.95)
    }).set_frame_rate(TARGET_SAMPLE_RATE)

    wav_buffer = io.BytesIO()
    audio_segment.export(wav_buffer, format="wav")
    return wav_buffer.getvalue()

# ====================== PLAY FUNCTION ======================
def play_audio(audio_data: bytes):
    """Play decoded audio using simpleaudio."""
    wave_obj = sa.WaveObject(audio_data, num_channels=TARGET_CHANNELS, bytes_per_sample=2, sample_rate=TARGET_SAMPLE_RATE)
    play_obj = wave_obj.play()
    play_obj.wait_done()

# ====================== SPEAK FUNCTION ======================
def speak_text(text: str):
    print(f"🧠 Speaking: {text}")
    audio_data = synthesize_speech(text)
    play_audio(audio_data)

# ====================== TEST ======================
if __name__ == "__main__":
    test_text = "Hello Shahid, this is ElevenLabs TTS. I now speak at a more natural pace."
    speak_text(test_text)

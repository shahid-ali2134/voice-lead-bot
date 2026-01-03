import os
from services.whisper_service import WhisperService
from services.ollama_service import OllamaService
from services.tts_service import TTSService
from config import INPUT_AUDIO_FILE, OUTPUT_AUDIO_FILE
from logger import get_logger

logger = get_logger(__name__)

class VoiceAgent:
    def __init__(self):
        logger.info("🤖 Initializing VoiceAgent...")
        self.whisper = WhisperService()
        self.ollama = OllamaService()
        self.tts = TTSService()
        logger.info("✅ VoiceAgent ready!")

    def process_audio(self, audio_file: str = INPUT_AUDIO_FILE) -> str:
        """
        Full pipeline:
        1. Transcribe audio → text
        2. Send text to Ollama
        3. Convert response to speech
        4. Return response audio path
        """
        logger.info(f"🎤 Processing audio file: {audio_file}")

        # Step 1: Transcribe
        text_input = self.whisper.transcribe(audio_file)
        logger.info(f"📝 Transcribed text: {text_input}")

        # Step 2: Ollama LLM response
        llm_response = self.ollama.generate(text_input)
        logger.info(f"🧠 LLM response: {llm_response}")

        # Step 3: TTS synthesis
        audio_output = self.tts.synthesize(llm_response, output_file=OUTPUT_AUDIO_FILE)

        logger.info(f"✅ VoiceAgent pipeline complete. Output: {os.path.abspath(audio_output)}")
        return audio_output


if __name__ == "__main__":
    agent = VoiceAgent()
    result_path = agent.process_audio()
    print(f"🔊 Final response audio file: {result_path}")

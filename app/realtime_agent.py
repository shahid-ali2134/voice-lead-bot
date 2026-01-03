import io
import os
import re
import json
import time
import threading
import queue
import sounddevice as sd
import numpy as np
import soundfile as sf
import simpleaudio as sa
from datetime import datetime

from vad_utils import VADDetector
from services.whisper_service import WhisperService
from services.ollama_service import OllamaService
from services.tts_service import TTSService
from routes.leads import LeadQualification
from logger import get_logger

logger = get_logger(__name__)

SAMPLE_RATE = 16000
FRAME_DURATION = 30  # ms
SILENCE_THRESHOLD = 20
LEADS_FILE = os.path.join(os.getcwd(), "leads.json")  # ✅ absolute path

TTS_QUEUE = queue.Queue()
TTS_STOP_EVENT = threading.Event()


class RealTimeAgentVAD:
    def __init__(self):
        self.whisper = WhisperService()
        self.ollama = OllamaService()
        self.tts = TTSService()
        self.vad = VADDetector(aggressiveness=2)
        self.lead_logic = LeadQualification()
        logger.info("🎧 RealTimeAgent with VAD initialized")

    # ====================== AUDIO RECORDING ======================
    def record_until_silence(self):
        logger.info("🎤 Start speaking...")
        buffer = []
        silence_frames = 0
        speech_frames = 0
        frame_samples = int(SAMPLE_RATE * FRAME_DURATION / 1000)

        sd.sleep(500)

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16') as stream:
            while True:
                audio_chunk, _ = stream.read(frame_samples)
                audio_bytes = audio_chunk.tobytes()

                if self.vad.is_speech(audio_bytes, SAMPLE_RATE):
                    buffer.append(audio_chunk)
                    silence_frames = 0
                    speech_frames += 1
                else:
                    if speech_frames > 5:
                        silence_frames += 1

                if speech_frames > 0 and silence_frames > SILENCE_THRESHOLD:
                    logger.info("🛑 Silence detected — stopping recording")
                    break

        if len(buffer) == 0:
            logger.warning("⚠️ No speech captured.")
            return None

        audio_data = np.concatenate(buffer, axis=0)
        wav_buffer = io.BytesIO()
        sf.write(wav_buffer, audio_data, SAMPLE_RATE, format='WAV')
        wav_buffer.seek(0)
        return wav_buffer

    # ====================== SPEECH TO TEXT ======================
    def transcribe(self, audio_buffer):
        transcription = self.whisper.transcribe(audio_buffer)
        return transcription.strip()

    # ====================== LEAD EXTRACTION HELPERS ======================
    def extract_name(self, text: str) -> str:
        text = text.strip().rstrip(".!?").strip()
        lowered = text.lower()

        intro_phrases = [
            "my name is", "i am", "i'm", "this is",
            "mi nombre es", "mein name ist", "mijn naam is", "je m'appelle",
        ]

        for phrase in intro_phrases:
            if lowered.startswith(phrase):
                name = text[len(phrase):].strip()
                name = re.sub(r"[^A-Za-z\s\-]", "", name)
                return name

        return re.sub(r"[^A-Za-z\s\-]", "", text).strip()

    def extract_company(self, text: str) -> str:
        """
        Extracts only the company name from common intro phrases like:
        'I am from Tech Terror Technologies' -> 'Tech Terror Technologies'
        """
        text = text.strip().rstrip(".!?").strip()
        lowered = text.lower()

        company_phrases = [
            "i work at",
            "i work for",
            "i am from",
            "i'm from",
            "my company is",
            "representing",
            "represent",
            "we are",
            "company name is",
            "i represent",
        ]

        for phrase in company_phrases:
            if lowered.startswith(phrase):
                company = text[len(phrase):].strip()
                # 🧹 Remove any leading prepositions like "the", "at", "from"
                company = re.sub(r"^(the|at|from)\s+", "", company, flags=re.IGNORECASE)
                # 🧼 Remove extra punctuation
                company = re.sub(r"[^A-Za-z0-9\s\-]", "", company)
                return company.strip()

        # fallback: clean any punctuation
        return re.sub(r"[^A-Za-z0-9\s\-]", "", text).strip()

    def extract_budget(self, text: str) -> str:
        text = text.replace(",", "")
        match = re.search(r"(\$?\d+)", text)
        if match:
            return match.group(1)
        return text

    def extract_interest(self, text: str) -> str:
        text = text.strip().rstrip(".!?").strip()
        lowered = text.lower()

        interest_phrases = [
            "i am interested in", "i'm interested in", "interested in",
            "my interest is", "i want", "i would like", "i need",
        ]

        for phrase in interest_phrases:
            if lowered.startswith(phrase):
                interest = text[len(phrase):].strip()
                interest = re.sub(r"[^A-Za-z0-9\s\-]", "", interest)
                return interest

        return re.sub(r"[^A-Za-z0-9\s\-]", "", text).strip()

    # ====================== TEXT TO SPEECH ======================
    def speak(self, text: str):
        try:
            chunks = re.split(r'(?<=[.!?])\s+', text.strip())
            clean_chunks = [
                c.strip()
                for c in chunks
                if c.strip() and not re.fullmatch(r'^[^\w]+$', c.strip())
            ]
            clean_text = " ".join(clean_chunks).strip()

            # 🧼 Fix duplicate "from from"
            clean_text = re.sub(r'\bfrom\s+from\b', 'from ', clean_text, flags=re.IGNORECASE)

            if not clean_text:
                logger.warning("⚠️ Nothing to speak after cleaning text.")
                return

            logger.info(f"🧠 Speaking cleaned text: {clean_text}")
            audio_buffer = self.tts.synthesize_to_memory(clean_text)
            wave_obj = sa.WaveObject(audio_buffer.read(), 1, 2, 22050)
            play_obj = wave_obj.play()
            play_obj.wait_done()

        except Exception as e:
            logger.error(f"❌ TTS synthesis/playback failed: {e}")

    # ====================== LLM RESPONSE ======================
    def generate_short_response(self, prompt: str):
        instruction = (
            "Answer in 1-2 sentences only. "
            "Keep it conversational and concise. "
            "Avoid repeating the user's exact phrasing."
        )
        full_prompt = f"{instruction}\nUser: {prompt}\nAssistant:"

        llm_response = ""
        for chunk in self.ollama.stream_generate(full_prompt):
            llm_response += chunk

        if len(llm_response) > 300:
            logger.warning("⚠️ Response too long, truncating for TTS.")
            llm_response = llm_response[:300] + "..."

        return llm_response.strip()

    # ====================== LEAD SAVING ======================
    def save_lead_to_json(self, lead_data: dict):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "lead": lead_data
        }

        try:
            if os.path.exists(LEADS_FILE):
                with open(LEADS_FILE, "r", encoding="utf-8") as f:
                    try:
                        leads = json.load(f)
                    except json.JSONDecodeError:
                        leads = []
            else:
                leads = []

            leads.append(entry)

            with open(LEADS_FILE, "w", encoding="utf-8") as f:
                json.dump(leads, f, indent=2)

            logger.info(f"💾 Lead saved to {LEADS_FILE}")
        except Exception as e:
            logger.error(f"❌ Failed to save lead: {e}")

    # ====================== MAIN LOOP ======================
    def run(self):
        logger.info("🤖 Real-time agent with VAD is running...")
        while True:
            audio_buffer = self.record_until_silence()
            if not audio_buffer:
                logger.info("⚠️ Nothing recorded, listening again...")
                continue

            text_input = self.transcribe(audio_buffer)
            if not text_input:
                logger.info("⚠️ No speech detected, listening again...")
                continue

            logger.info(f"📝 You said: {text_input}")

            if not self.lead_logic.is_qualified():
                state = self.lead_logic.state
                if state == "ask_name":
                    text_input = self.extract_name(text_input)
                elif state == "ask_company":
                    text_input = self.extract_company(text_input)
                elif state == "ask_budget":
                    text_input = self.extract_budget(text_input)
                elif state == "ask_interest":
                    text_input = self.extract_interest(text_input)

                bot_response = self.lead_logic.next_prompt(text_input)
                logger.info(f"🏷 Lead qualification step. State: {state}")

                if self.lead_logic.is_qualified():
                    lead_data = self.lead_logic.get_lead_data()

                    if "name" in lead_data:
                        lead_data["name"] = self.extract_name(lead_data["name"])
                    if "company" in lead_data:
                        lead_data["company"] = self.extract_company(lead_data["company"])
                    if "budget" in lead_data:
                        lead_data["budget"] = self.extract_budget(lead_data["budget"])
                    if "interest" in lead_data:
                        lead_data["interest"] = self.extract_interest(lead_data["interest"])

                    logger.info(f"📥 Lead qualified and captured: {lead_data}")
                    self.save_lead_to_json(lead_data)

                    # 🧠 Add goodbye message after qualification
                    bot_response += " Bye!"

            else:
                bot_response = self.generate_short_response(text_input)
                logger.info(f"✅ Final LLM response: {bot_response}")

            self.speak(bot_response)


# ====================== ENTRY POINT ======================
if __name__ == "__main__":
    try:
        agent = RealTimeAgentVAD()
        agent.run()
    except KeyboardInterrupt:
        TTS_STOP_EVENT.set()
        logger.info("👋 Exiting gracefully...")

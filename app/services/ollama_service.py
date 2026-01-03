import requests
import json
from config import OLLAMA_API_URL, OLLAMA_MODEL
from logger import get_logger

logger = get_logger(__name__)


class OllamaService:
    def __init__(self, model: str = OLLAMA_MODEL):
        self.model = model
        logger.info(f"🧠 OllamaService initialized with model: {self.model}")

    def generate(self, prompt: str) -> str:
        """
        Non-streaming fallback (synchronous).
        """
        url = f"{OLLAMA_API_URL}/api/generate"
        payload = {"model": self.model, "prompt": prompt, "stream": False}

        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

    def stream_generate(self, prompt: str):
        """
        Stream chunks of LLM response as they are generated.
        """
        url = f"{OLLAMA_API_URL}/api/generate"
        payload = {"model": self.model, "prompt": prompt, "stream": True}

        with requests.post(url, json=payload, stream=True) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line.decode("utf-8"))
                    chunk = data.get("response", "")
                    if chunk:
                        yield chunk
                    if data.get("done"):
                        break
                except Exception as e:
                    logger.error(f"❌ Stream parse error: {e}")
                    continue

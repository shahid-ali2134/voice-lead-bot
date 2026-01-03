# test_ollama_service.py
from services.ollama_service import OllamaService

ollama = OllamaService()
response = ollama.generate("Hello, how are you?")
print("🤖 Ollama:", response)

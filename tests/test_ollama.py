import requests
import json

def ask_ollama(prompt: str):
    url = "http://localhost:11434/api/generate"
    response = requests.post(url, json={"model": "llama3", "prompt": prompt}, stream=True)

    print("🧠 Ollama Response:")
    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode('utf-8'))
            if "response" in data:
                print(data["response"], end="", flush=True)

if __name__ == "__main__":
    ask_ollama("Say: Hello from LLaMA 3!")

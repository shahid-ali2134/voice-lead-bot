import asyncio
import websockets
import base64
import io
from realtime_agent import RealTimeAgentVAD  # ✅ correct class name

# Initialize your AI agent
agent = RealTimeAgentVAD()

async def handler(websocket):
    print("✅ Client connected")

    try:
        async for message in websocket:
            # Decode Base64 → bytes
            audio_bytes = base64.b64decode(message)

            # Convert to in-memory WAV file for Whisper
            audio_stream = io.BytesIO(audio_bytes)

            # Transcribe and generate reply
            text = agent.transcribe(audio_stream)
            print(f"🗣️ User said: {text}")

            bot_reply = agent.generate_short_response(text)
            print(f"🤖 Agent reply: {bot_reply}")

            # Generate speech for response
            tts_audio = agent.tts.synthesize_to_memory(bot_reply)
            audio_data = tts_audio.read()

            # Send back to frontend as Base64 audio
            await websocket.send(base64.b64encode(audio_data).decode("utf-8"))

    except websockets.exceptions.ConnectionClosed:
        print("❌ Client disconnected")

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("🎧 WebSocket voice server running on ws://localhost:8765")
        await asyncio.Future()  # Keep server alive

if __name__ == "__main__":
    asyncio.run(main())

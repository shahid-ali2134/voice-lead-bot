import asyncio
import base64
import json
import websockets

WAV_PATH = "test_audio.wav"

async def run():
    async with websockets.connect("ws://localhost:8765") as ws:
        # Initial messages from server
        print("INIT:", await ws.recv())
        print("INIT:", await ws.recv())

        with open(WAV_PATH, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        await ws.send(json.dumps({"type": "audio", "b64": b64}))

        # Print responses until we get an agent reply (or error)
        for _ in range(10):
            msg = await ws.recv()
            print("RX:", msg)
            if '"type": "error"' in msg:
                break

asyncio.run(run())

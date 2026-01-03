# ws_server.py
import asyncio
import base64
import io
import json
import os
import tempfile
import time
import wave

import websockets

from realtime_agent_v2 import RealTimeAgentVAD, SAMPLE_RATE, FRAME_DURATION  # uses your integrated pipeline :contentReference[oaicite:1]{index=1}
from vad_utils import VADDetector


LEADS_FILE = "leads.json"


def load_leads():
    if not os.path.exists(LEADS_FILE):
        return []
    try:
        with open(LEADS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_lead(lead: dict):
    lead = dict(lead)
    lead["timestamp"] = time.time()
    leads = load_leads()
    leads.append(lead)
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2)


def wav_b64_from_text(agent: RealTimeAgentVAD, text: str) -> str:
    # uses your ElevenLabs TTS memory synth :contentReference[oaicite:2]{index=2}
    audio_buf = agent.tts.synthesize_to_memory(text)
    return base64.b64encode(audio_buf.read()).decode("utf-8")


def wav_is_speech_by_webrtcvad(wav_path: str, vad: VADDetector) -> bool:
    """
    Returns True if webrtcvad detects speech in enough frames.
    WAV must be 16kHz mono 16-bit PCM (frontend will send that).
    """
    with wave.open(wav_path, "rb") as wf:
        ch = wf.getnchannels()
        sw = wf.getsampwidth()
        sr = wf.getframerate()

        if ch != 1 or sw != 2 or sr != SAMPLE_RATE:
            # If format mismatch, don't hard-fail the demo; just allow it through.
            return True

        frame_ms = FRAME_DURATION  # 30ms in your pipeline :contentReference[oaicite:3]{index=3}
        frame_samples = int(sr * frame_ms / 1000)
        bytes_per_frame = frame_samples * 2  # int16 mono

        speech_frames = 0
        total_frames = 0

        while True:
            frame = wf.readframes(frame_samples)
            if not frame:
                break
            if len(frame) < bytes_per_frame:
                break

            total_frames += 1
            if vad.is_speech(frame, sr):
                speech_frames += 1

        if total_frames == 0:
            return False

        # Require at least a few speech frames (filters random short noise)
        return speech_frames >= 3


async def handler(websocket):
    agent = RealTimeAgentVAD()  # integrated lead flow + extractors :contentReference[oaicite:4]{index=4}
    vad = VADDetector(aggressiveness=2)

    flow = agent.lead_logic  # LeadQualification inside your agent :contentReference[oaicite:5]{index=5}

    # Initial prompt
    await websocket.send(json.dumps({"type": "state", "value": flow.state}))
    prompt = flow.next_prompt()
    await websocket.send(json.dumps({"type": "agent_text", "text": prompt}))

    # Tell frontend "agent speaking", send audio, then "agent done"
    await websocket.send(json.dumps({"type": "agent_speaking", "value": True}))
    await websocket.send(json.dumps({"type": "tts_audio", "mime": "audio/wav", "b64": wav_b64_from_text(agent, prompt)}))
    await websocket.send(json.dumps({"type": "agent_speaking", "value": False}))

    async for msg in websocket:
        try:
            payload = json.loads(msg)
        except Exception:
            await websocket.send(json.dumps({"type": "error", "message": "Expected JSON message"}))
            continue

        msg_type = payload.get("type")

        if msg_type == "reset":
            agent = RealTimeAgentVAD()
            vad = VADDetector(aggressiveness=2)
            flow = agent.lead_logic

            await websocket.send(json.dumps({"type": "tell", "message": "reset_ok"}))
            await websocket.send(json.dumps({"type": "state", "value": flow.state}))

            prompt = flow.next_prompt()
            await websocket.send(json.dumps({"type": "agent_text", "text": prompt}))
            await websocket.send(json.dumps({"type": "agent_speaking", "value": True}))
            await websocket.send(json.dumps({"type": "tts_audio", "mime": "audio/wav", "b64": wav_b64_from_text(agent, prompt)}))
            await websocket.send(json.dumps({"type": "agent_speaking", "value": False}))
            continue

        if msg_type != "audio":
            await websocket.send(json.dumps({"type": "error", "message": "Unknown message type"}))
            continue

        b64 = payload.get("b64")
        if not b64:
            await websocket.send(json.dumps({"type": "error", "message": "Missing b64 field"}))
            continue

        try:
            audio_bytes = base64.b64decode(b64)
        except Exception:
            await websocket.send(json.dumps({"type": "error", "message": "Invalid base64 audio"}))
            continue

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            # ✅ webrtcvad gate: ignore random/noise clips
            if not wav_is_speech_by_webrtcvad(tmp_path, vad):
                await websocket.send(json.dumps({"type": "vad", "value": "no_speech"}))
                continue

            # Transcribe (your WhisperService expects file path) :contentReference[oaicite:6]{index=6}
            text = (agent.whisper.transcribe(tmp_path) or "").strip()
            if not text:
                await websocket.send(json.dumps({"type": "vad", "value": "empty_transcript"}))
                continue

            await websocket.send(json.dumps({"type": "user_text", "text": text}))

            # ✅ IMPORTANT: use your extractor so “my name is shahid” becomes “shahid”
            # matches your logic in run(): :contentReference[oaicite:7]{index=7}
            state = flow.state
            if state == "ask_name":
                text = agent.extract_name(text)  # :contentReference[oaicite:8]{index=8}
            elif state == "ask_company":
                text = agent.extract_company(text)  # :contentReference[oaicite:9]{index=9}
            elif state == "ask_budget":
                text = agent.extract_budget(text)  # :contentReference[oaicite:10]{index=10}
            elif state == "ask_interest":
                text = agent.extract_interest(text)  # :contentReference[oaicite:11]{index=11}

            agent_reply = flow.next_prompt(text)

            await websocket.send(json.dumps({"type": "state", "value": flow.state}))
            await websocket.send(json.dumps({"type": "agent_text", "text": agent_reply}))

            await websocket.send(json.dumps({"type": "agent_speaking", "value": True}))
            await websocket.send(json.dumps({"type": "tts_audio", "mime": "audio/wav", "b64": wav_b64_from_text(agent, agent_reply)}))
            await websocket.send(json.dumps({"type": "agent_speaking", "value": False}))

            if flow.is_qualified():
                lead = flow.get_lead_data()
                save_lead(lead)
                await websocket.send(json.dumps({"type": "lead", "data": lead}))

        except Exception as e:
            await websocket.send(json.dumps({"type": "error", "message": str(e)}))
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass


async def main():
    print("WebSocket server running on ws://localhost:8765")
    async with websockets.serve(handler, "localhost", 8765, max_size=20 * 1024 * 1024):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())

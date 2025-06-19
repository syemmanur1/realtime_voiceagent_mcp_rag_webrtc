# webrtc_server/app.py
import asyncio
import json
import os
import aiohttp
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaStreamTrack
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech_v1 as texttospeech

# --- Configuration ---
# Service URLs
AGENT_URL = os.environ.get("AGENT_URL", "http://localhost:8080")
MCP_URL = os.environ.get("MCP_URL", "http://localhost:8081") # For self-hosted models
# Authentication
MCP_AUTH_TOKEN = os.environ.get("MCP_AUTH_TOKEN")
# Provider Selection (set in your environment)
STT_PROVIDER = os.environ.get("STT_PROVIDER", "google") # 'google' or 'self-hosted'
TTS_PROVIDER = os.environ.get("TTS_PROVIDER", "google") # 'google' or 'self-hosted'
# Server Port
PORT = int(os.environ.get("PORT", 8000))
# Google Cloud Config
GOOGLE_STT_LANGUAGE_CODE = "en-US"
GOOGLE_TTS_LANGUAGE_CODE = "en-US"
GOOGLE_TTS_VOICE_NAME = "en-US-Standard-J"

# --- WebRTC Media Track ---
class AudioStreamer(MediaStreamTrack):
    kind = "audio"
    def __init__(self, track):
        super().__init__()
        self.track = track

    async def recv(self):
        return await self.track.recv()

# --- STT Service Routers ---

async def stt_router(audio_streamer):
    if STT_PROVIDER == 'google':
        async for text in stream_to_google_stt(audio_streamer):
            yield text
    elif STT_PROVIDER == 'self-hosted':
        async with aiohttp.ClientSession() as session:
            async for text in stream_to_mcp_stt(audio_streamer, session):
                yield text
    else:
        raise ValueError(f"Invalid STT_PROVIDER: {STT_PROVIDER}")

async def stream_to_google_stt(audio_streamer):
    client = speech.SpeechAsyncClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=48000,
        language_code=GOOGLE_STT_LANGUAGE_CODE,
        enable_automatic_punctuation=True,
    )
    streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)

    async def audio_generator():
        yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)
        while True:
            try:
                frame = await audio_streamer.recv()
                # Google STT requires raw PCM_16 data
                yield speech.StreamingRecognizeRequest(audio_content=frame.tobytes())
            except Exception:
                break
    
    responses = await client.streaming_recognize(requests=audio_generator())
    async for response in responses:
        for result in response.results:
            if result.is_final:
                yield {"text": result.alternatives[0].transcript, "is_final": True}

async def stream_to_mcp_stt(audio_streamer, session):
    stt_endpoint = f"{MCP_URL}/stt"
    headers = {"Authorization": f"Bearer {MCP_AUTH_TOKEN}"}
    async with session.post(stt_endpoint, headers=headers, data=audio_streamer) as resp:
        async for line in resp.content:
            yield json.loads(line)

# --- TTS Service Routers ---
async def tts_router(text_stream):
    if TTS_PROVIDER == 'google':
        async for audio_chunk in stream_from_google_tts(text_stream):
            yield audio_chunk
    elif TTS_PROVIDER == 'self-hosted':
        async with aiohttp.ClientSession() as session:
            async for audio_chunk in stream_to_mcp_tts(text_stream, session):
                yield audio_chunk
    else:
        raise ValueError(f"Invalid TTS_PROVIDER: {TTS_PROVIDER}")

async def stream_from_google_tts(text_stream):
    client = texttospeech.TextToSpeechAsyncClient()
    voice = texttospeech.VoiceSelectionParams(language_code=GOOGLE_TTS_LANGUAGE_CODE, name=GOOGLE_TTS_VOICE_NAME)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    
    async for text_data in text_stream:
        synthesis_input = texttospeech.SynthesisInput(text=text_data["text_chunk"])
        response = await client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        yield response.audio_content

async def stream_to_mcp_tts(text_stream, session):
    tts_endpoint = f"{MCP_URL}/tts"
    headers = {"Authorization": f"Bearer {MCP_AUTH_TOKEN}"}
    async with session.post(tts_endpoint, headers=headers, data=text_stream) as resp:
        async for chunk in resp.content.iter_chunked(1024):
            yield chunk

# --- Core Orchestration Logic ---

async def stream_to_agent(stt_stream, session):
    agent_endpoint = f"{AGENT_URL}/stream"
    async def text_generator():
        async for stt_result in stt_stream:
            yield json.dumps(stt_result) + "\n"
    async with session.post(agent_endpoint, data=text_generator()) as resp:
        async for line in resp.content:
            yield json.loads(line)

async def handle_conversation_stream(ws, audio_streamer):
    """Orchestrates the full data pipeline."""
    async with aiohttp.ClientSession() as session:
        stt_stream = stt_router(audio_streamer)
        agent_stream = stream_to_agent(stt_stream, session)
        tts_audio_stream = tts_router(agent_stream)
        
        async for audio_chunk in tts_audio_stream:
            try:
                await ws.send_bytes(audio_chunk)
            except ConnectionResetError:
                print("Client connection closed.")
                break

# --- WebSocket & WebRTC Connection Handling ---

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    pc = RTCPeerConnection()

    @pc.on("track")
    async def on_track(track):
        if track.kind == "audio":
            audio_streamer = AudioStreamer(track)
            await handle_conversation_stream(ws, audio_streamer)

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            data = json.loads(msg.data)
            if data["type"] == "offer":
                await pc.setRemoteDescription(RTCSessionDescription(sdp=data["sdp"], type=data["type"]))
                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)
                await ws.send_json({"type": "answer", "sdp": pc.localDescription.sdp})
    
    await pc.close()
    return ws

# --- Application Setup ---
app = web.Application()
app.router.add_get("/ws", websocket_handler)

if __name__ == "__main__":
    web.run_app(app, port=PORT)

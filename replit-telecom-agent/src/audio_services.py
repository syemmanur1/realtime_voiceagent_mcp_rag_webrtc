# telecom_agent/src/audio_services.py
import requests
from config import MCP_SERVER_URL, MCP_AUTH_TOKEN

def transcribe_audio_via_mcp(audio_bytes, filename="audio.webm"):
    """
    Calls the self-hosted MCP server to transcribe audio.
    """
    if not MCP_SERVER_URL or not MCP_AUTH_TOKEN:
        raise ValueError("MCP Server URL or Auth Token is not configured.")
        
    stt_endpoint = f"{MCP_SERVER_URL}/stt"
    headers = {"Authorization": f"Bearer {MCP_AUTH_TOKEN}"}
    files = {'file': (filename, audio_bytes, 'audio/webm')}
    
    try:
        response = requests.post(stt_endpoint, headers=headers, files=files)
        response.raise_for_status()
        return response.json()['text']
    except requests.exceptions.RequestException as e:
        print(f"Error calling MCP STT service: {e}")
        return ""

def synthesize_speech_via_mcp(text_to_speak):
    """
    Calls the self-hosted MCP server to synthesize speech.
    """
    if not MCP_SERVER_URL or not MCP_AUTH_TOKEN:
        raise ValueError("MCP Server URL or Auth Token is not configured.")
        
    tts_endpoint = f"{MCP_SERVER_URL}/tts"
    headers = {"Authorization": f"Bearer {MCP_AUTH_TOKEN}"}
    payload = {"text": text_to_speak}
    
    try:
        response = requests.post(tts_endpoint, headers=headers, json=payload)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error calling MCP TTS service: {e}")
        return None

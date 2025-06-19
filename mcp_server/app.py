# mcp_server/app.py
import os
import torch
from flask import Flask, request, jsonify, send_file
from transformers import pipeline
from chatterbox import Chatterbox
from google.cloud import speech
from google.cloud import texttospeech
import tempfile
import io

# --- Initialization ---
app = Flask(__name__)

# --- Provider Configuration ---
# Set via environment variables. Defaults to 'self-hosted'.
STT_PROVIDER = os.environ.get('STT_PROVIDER', 'self-hosted')
TTS_PROVIDER = os.environ.get('TTS_PROVIDER', 'self-hosted')

# --- Google Cloud Configuration ---
# Assumes GOOGLE_APPLICATION_CREDENTIALS is set in the environment
GOOGLE_TTS_LANGUAGE_CODE = "en-US"
GOOGLE_TTS_VOICE_NAME = "en-US-Standard-J"
GOOGLE_STT_LANGUAGE_CODE = "en-US"

# --- Conditional Model Loading ---

# Load self-hosted models only if they are selected as a provider
if 'self-hosted' in [STT_PROVIDER, TTS_PROVIDER]:
    print("Initializing self-hosted models...")
    # Whisper STT Model
    if STT_PROVIDER == 'self-hosted':
        device = 0 if torch.cuda.is_available() else -1
        print(f"Whisper using device: {'GPU' if device == 0 else 'CPU'}")
        stt_pipe = pipeline("automatic-speech-recognition", model="distil-whisper/distil-large-v2", device=device)
        print("Whisper STT model loaded.")
    # Chatterbox TTS Model
    if TTS_PROVIDER == 'self-hosted':
        tts_model = Chatterbox()
        print("Chatterbox TTS model loaded.")

# Initialize Google clients only if they are selected as a provider
if 'google' in [STT_PROVIDER, TTS_PROVIDER]:
    print("Initializing Google Cloud clients...")
    if STT_PROVIDER == 'google':
        google_speech_client = speech.SpeechClient()
        print("Google Speech-to-Text client initialized.")
    if TTS_PROVIDER == 'google':
        google_tts_client = texttospeech.TextToSpeechClient()
        print("Google Text-to-Speech client initialized.")


# --- Authentication ---
def check_auth():
    auth_header = request.headers.get('Authorization')
    expected_token = f"Bearer {os.environ.get('MCP_AUTH_TOKEN')}"
    return auth_header and auth_header == expected_token

# --- Internal Provider Functions ---

def _stt_self_hosted(file):
    with tempfile.NamedTemporaryFile(delete=True, suffix=".webm") as temp_audio:
        file.save(temp_audio.name)
        result = stt_pipe(temp_audio.name)
    return result['text']

def _stt_google(file):
    content = file.read()
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        sample_rate_hertz=48000,
        language_code=GOOGLE_STT_LANGUAGE_CODE,
    )
    response = google_speech_client.recognize(config=config, audio=audio)
    if response.results and response.results[0].alternatives:
        return response.results[0].alternatives[0].transcript
    return ""

def _tts_self_hosted(text):
    audio_bytes = tts_model.synthesize(text)
    return send_file(io.BytesIO(audio_bytes), mimetype='audio/wav')

def _tts_google(text):
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=GOOGLE_TTS_LANGUAGE_CODE, name=GOOGLE_TTS_VOICE_NAME
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = google_tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    return send_file(io.BytesIO(response.audio_content), mimetype='audio/mpeg')

# --- API Endpoints ---

@app.route('/stt', methods=['POST'])
def speech_to_text():
    if not check_auth(): return jsonify({"error": "Unauthorized"}), 401
    if 'file' not in request.files: return jsonify({"error": "No audio file part"}), 400
    
    file = request.files['file']
    try:
        if STT_PROVIDER == 'self-hosted':
            transcribed_text = _stt_self_hosted(file)
        elif STT_PROVIDER == 'google':
            transcribed_text = _stt_google(file)
        else:
            return jsonify({"error": f"Invalid STT provider configured: {STT_PROVIDER}"}), 500
        
        return jsonify({"text": transcribed_text})
    except Exception as e:
        print(f"Error during STT processing with {STT_PROVIDER}: {e}")
        return jsonify({"error": "Failed to process audio file"}), 500

@app.route('/tts', methods=['POST'])
def text_to_speech():
    if not check_auth(): return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    if not data or 'text' not in data: return jsonify({"error": "Text not provided"}), 400
    
    text = data.get('text')
    try:
        if TTS_PROVIDER == 'self-hosted':
            return _tts_self_hosted(text)
        elif TTS_PROVIDER == 'google':
            return _tts_google(text)
        else:
            return jsonify({"error": f"Invalid TTS provider configured: {TTS_PROVIDER}"}), 500
    except Exception as e:
        print(f"Error during TTS synthesis with {TTS_PROVIDER}: {e}")
        return jsonify({"error": "Failed to synthesize speech"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8081)))

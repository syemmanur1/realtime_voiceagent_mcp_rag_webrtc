# telecom_agent/src/main.py
import os
import json
from flask import Flask, request, Response
from config import GOOGLE_API_KEY
from rag_pipeline import agent_pipeline
from context import get_context, add_to_context
from speech_enhancer import filter_for_tts

app = Flask(__name__)

def stream_processor():
    """
    Receives a stream of STT results, processes them, and yields
    agent response chunks.
    """
    session_id = "streaming_session" 
    full_transcript = []

    for line in request.stream:
        if line:
            stt_result = json.loads(line.decode('utf-8'))
            transcript_chunk = stt_result.get("text", "")
            
            if transcript_chunk:
                full_transcript.append(transcript_chunk)
                
                if stt_result.get("is_final", True): 
                    final_query = "".join(full_transcript)
                    print(f"Processing Query: {final_query}")
                    
                    history = get_context(session_id)
                    response_text = agent_pipeline(final_query, history)
                    add_to_context(session_id, final_query, response_text)
                    
                    clean_response = filter_for_tts(response_text)
                    
                    for word in clean_response.split():
                        yield json.dumps({"text_chunk": word + " "}) + "\n"
                    
                    full_transcript = []

@app.route('/stream', methods=['POST'])
def agent_stream_handler():
    return Response(stream_processor(), mimetype='application/json')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

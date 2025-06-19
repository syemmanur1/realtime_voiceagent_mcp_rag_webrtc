# telecom_agent/src/main.py
import os
import json
from flask import Flask, request, jsonify, Response
from config import GOOGLE_API_KEY
# Renamed import to avoid function name conflicts
from rag_pipeline import agent_pipeline as run_agent_pipeline
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
                    # The pipeline now returns a dictionary
                    pipeline_result = run_agent_pipeline(final_query, history)
                    response_text = pipeline_result["response_text"]
                    retrieved_docs = pipeline_result["retrieved_doc_ids"]

                    # Log the retrieved docs for inspection during streaming tests
                    print(f"Retrieved docs for query: {retrieved_docs}")

                    add_to_context(session_id, final_query, response_text)
                    
                    clean_response = filter_for_tts(response_text)
                    
                    for word in clean_response.split():
                        yield json.dumps({"text_chunk": word + " "}) + "\n"
                    
                    full_transcript = []

@app.route('/stream', methods=['POST'])
def agent_stream_handler():
    return Response(stream_processor(), mimetype='application/json')

# --- New Test Endpoint ---
@app.route('/test-rag', methods=['POST'])
def test_rag_handler():
    """
    A simple endpoint to test the RAG pipeline directly with text.
    """
    data = request.json
    if not data or 'query' not in data:
        return jsonify({"error": "Query not provided"}), 400
    
    query = data['query']
    session_id = data.get('session_id', 'test_session')
    history = get_context(session_id)
    
    try:
        pipeline_result = run_agent_pipeline(query, history)
        add_to_context(session_id, query, pipeline_result["response_text"])
        return jsonify(pipeline_result)
    except Exception as e:
        print(f"Error in /test-rag handler: {e}")
        return jsonify({"error": "An internal error occurred"}), 500

if __name__ == '__main__':
    # Ensure the telecom_agent runs on port 8080 as per the README
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

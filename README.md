```
[realtime_voiceagent_mcp_rag_webrtc]/
├── webrtc_server/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
│
├── mcp_server/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
│
├── telecom_agent/
│   ├── .replit
│   ├── pyproject.toml
│   ├── replit.nix
│   ├── knowledge_base/
│   │   ├── documents/
│   │   └── metadata/
│   ├── scripts/
│   │   └── initialize_kb.py
│   └── src/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── context.py
│       ├── ingestion.py
│       ├── rag_pipeline.py
│       ├── speech_enhancer.py
│       └── audio_services.py
│
└── android_client/
    └── app/
        ├── build.gradle.kts  <- (Module level gradle file)
        └── src/
            └── main/
                ├── java/
                │   └── com/yourcompany/telecomagent/
                │       ├── MainActivity.kt
                │       ├── SignalingClient.kt
                │       └── WebRtcClient.kt
                ├── res/
                │   └── layout/
                │       └── activity_main.xml
                └── AndroidManifest.xml

This structure organizes the project into four distinct, self-contained components:
webrtc_server: The lightweight entrypoint that handles all real-time communication with the client.
mcp_server: The optional, heavy-lifting service for hosting your own AI models for STT/TTS.
telecom_agent: The core application that contains the agentic RAG pipeline and conversational logic.
android_client: The native Android application that the end-user interacts with.


https://docs.google.com/document/d/1hvfff2dgJmmAojzIb9qikhdiYlbY3NS354Cxzue_3Tg/edit?usp=sharing

Real-Time Telecom Voice Agent

This project is a complete, production-ready framework for building a real-time, streaming conversational AI voice agent. It is designed for telecom customer support, featuring a sophisticated Retrieval-Augmented Generation (RAG) pipeline for knowledge base integration, but is extensible to any domain. The architecture is modular, scalable, and optimized for low-latency interactions, providing a flexible choice between cloud-based AI services and self-hosted models.

Architecture Overview
The system is composed of four distinct, decoupled services that communicate via real-time streams and internal APIs. This microservices architecture ensures scalability, maintainability, and fault tolerance.

WebRTC Server (webrtc_server)
Role: The real-time communication gateway and entrypoint for all clients.
Function: Manages WebSocket signaling and establishes WebRTC peer connections. It handles the "hot path" for media, streaming user audio directly to the chosen Speech-to-Text service and streaming the synthesized voice back to the client.
Key Feature: Acts as a router for audio services. It can call Google's low-latency STT/TTS APIs directly (default) or delegate to the mcp_server for self-hosted models.

Telecom Agent (telecom_agent)
Role: The "brain" of the operation.
Function: Contains the core business logic. It receives a stream of text from the webrtc_server, processes it through a hybrid RAG pipeline (using ChromaDB and Whoosh), queries the Gemini LLM for a response, and streams the generated text back. It has no knowledge of audio processing.

MCP Server (mcp_server)
Role: An optional, resource-intensive "toolbox" for self-hosted AI models.
Function: Hosts heavy models like Whisper (STT) and Chatterbox (TTS). It's designed to run on powerful hardware (ideally with a GPU) and is only used when the webrtc_server is configured to delegate requests to it. This keeps the core services lightweight.

Android Client (android_client)
Role: The end-user interface.Function: A native Android application that connects to the webrtc_server, streams microphone audio, and plays the incoming audio response from the agent in real-time.

Running Locally for Development

This setup allows you to run all services on your local machine, giving you more control for debugging and development.
1. Prerequisites
Python 3.10+ and pip installed.
Virtual Environments: It's highly recommended to use a tool like venv or conda to manage dependencies for each service.
Docker (Optional): If you plan to build container images, Docker Desktop is required. For simply running the Python scripts, it's not needed.

2. Initial Setup
Clone the Repository: Download the entire project to your local machine.
Set Environment Variables: You'll need to set environment variables in each terminal session before running a service. A convenient way is to create a shell script (e.g., start_dev.sh) in each service directory.

Example start_dev.sh for mcp_server:#!/bin/bash
export MCP_AUTH_TOKEN='your-strong-secret-token'

# To use self-hosted models (default)
export STT_PROVIDER='self-hosted'
export TTS_PROVIDER='self-hosted'

# Or uncomment to use Google APIs
# export STT_PROVIDER='google'
# export TTS_PROVIDER='google'
# export GOOGLE_APPLICATION_CREDENTIALS='/path/to/your/gcp-key.json'

python app.py
Install Dependencies: For each of the three server directories (telecom_agent, mcp_server, webrtc_server), navigate into the folder in your terminal and run pip install -r requirements.txt (or the equivalent for your environment manager).

Initialize Knowledge Base: In your terminal, navigate to the telecom_agent directory and run the one-time ingestion script:python scripts/initialize_kb.py

3. Running the Services
You will need three separate terminal windows.

Terminal 1: Run the mcp_server
Navigate to the directory: cd mcp_serverSet environment variables as described above.
Run the app: python app.py(This will start on http://localhost:8081. Leave this terminal running.)

Terminal 2: Run the telecom_agent
Navigate to the directory: cd telecom_agent
Set environment variables:
export GOOGLE_API_KEY='your-gemini-key'
export MCP_URL='http://localhost:8081'
export MCP_AUTH_TOKEN='your-secret-token' 

Run the app: python src/main.py (This will start on http://localhost:8080. Leave this terminal running.)

Terminal 3: Run the webrtc_server
Navigate to the directory: cd webrtc_server
Set environment variables:
export AGENT_URL='http://localhost:8080'
export MCP_URL='http://localhost:8081'
export MCP_AUTH_TOKEN='your-secret-token'
# Set providers to 'self-hosted' to test the mcp_server
export STT_PROVIDER='self-hosted'
export TTS_PROVIDER='self-hosted'

Run the app: python app.py (This will start on http://localhost:8000. Leave this terminal running.)

4. Testing the Backend
Use the provided webrtc_test.html file on your local computer. Update the WebSocket URL inside the file to point to your local instance: ws://localhost:8000/ws.
Open the HTML file in a browser to test the full pipeline.

Running in a Development Environment (Replit)

This setup allows you to run all services simultaneously within a single Replit project for development and testing.

1. Initial SetupSet Secrets: In your Replit project, go to the Secrets tab (under Tools). Set the following:
GOOGLE_API_KEY: Your API key for the Google Gemini LLM.
MCP_AUTH_TOKEN: Create a strong, unique password (e.g., secret-token-for-mcp-123). This will secure the communication between the services.
Optional: GOOGLE_APPLICATION_CREDENTIALS: Paste the entire content of your Google Cloud Service Account JSON file here if you want to use Google's STT/TTS APIs.

Initialize Knowledge Base: Open the Shell tab and run the one-time ingestion script. This will build your vector database.
python telecom_agent/scripts/initialize_kb.py

2. Running the Services
You will need three separate Shell tabs to run the three servers.

Tab 1: Run the mcp_server (Self-Hosted Models)
Navigate to the directory: cd mcp_server
Install dependencies: pip install -r requirements.txt
Set the auth token:
export MCP_AUTH_TOKEN='your-secret-token-for-mcp-123'
Run the app: python app.py (This will start on port 8081. Leave this tab running.)

Tab 2: Run the webrtc_server (Real-Time Gateway)
Navigate to the directory: cd webrtc_server
Install dependencies: pip install -r requirements.txt
Set environment variables, pointing to your other services.
Get your Replit URL (e.g., https://my-agent.replit.dev).
export AGENT_URL='https://my-agent.replit.dev:8080'
export MCP_URL='https://my-agent.replit.dev:8081'
export MCP_AUTH_TOKEN='your-secret-token-for-mcp-123'
# Set providers to 'self-hosted' to test the mcp_server
export STT_PROVIDER='self-hosted'
export TTS_PROVIDER='self-hosted'

Run the app:
python app.py (This will start on port 8000. Leave this tab running.)

Tab 3: Run the telecom_agent (Main Logic)
Set the entrypoint in your telecom_agent/.replit file to src/main.py.
Click the main Replit ▶ Run button.(This will use the Secrets you set in Step 1 and start the agent on port 8080.)

3. Testing the Backend
Use the provided webrtc_test.html file on your local computer. Update the WebSocket URL inside the file to point to your Replit instance (wss://my-agent.replit.dev/ws) and open it in a browser to test the full pipeline.

Running in a Production Environment (GCP)

This guide assumes you will deploy the services as containerized applications on Google Cloud Run.

1. Prerequisites
Google Cloud SDK (gcloud) installed and configured.
Docker installed on your local machine.
A GCP project with Cloud Run, Artifact Registry, and the required AI/ML APIs enabled.

2. Build and Push Docker Images
For both the webrtc_server and mcp_server directories:
Navigate into the service directory (e.g., cd mcp_server).
Build the image:
docker build -t us-central1-docker.pkg.dev/YOUR_PROJECT_ID/services/mcp-server:latest .

Push the image to Artifact Registry:
docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/services/mcp-server:latest

(Repeat for webrtc_server with a different image name.)

3. Deploy to Cloud Run
Deploy mcp_server (The Heavy Model Server):
gcloud run deploy mcp-server \
  --image=us-central1-docker.pkg.dev/YOUR_PROJECT_ID/services/mcp-server:latest \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars="MCP_AUTH_TOKEN=your-production-secret-token" \
  --cpu=2 --memory=8Gi --timeout=300 --concurrency=4
Note the higher CPU and memory allocation.

Deploy webrtc_server (The Gateway):
After deploying, Cloud Run will provide a service URL for the mcp-server. Use it here.
gcloud run deploy webrtc-server \
  --image=us-central1-docker.pkg.dev/YOUR_PROJECT_ID/services/webrtc-server:latest \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars="MCP_URL=https://mcp-server-xyz-uc.a.run.app,MCP_AUTH_TOKEN=your-production-secret-token,AGENT_URL=https://telecom-agent-xyz-uc.a.run.app"

Deploy telecom_agent:
This service can also be containerized and deployed to Cloud Run with its own set of environment variables pointing to the deployed webrtc_server.

4. Android Client Configuration
Finally, update the android_client to point to your production webrtc_server.
In MainActivity.kt, change the serverUrl variable to your production Cloud Run WebSocket URL.
Note that Cloud Run does not support WebSockets out of the box; you may need to front it with a load balancer or use a different service like Google Kubernetes Engine for full WebRTC support in production.

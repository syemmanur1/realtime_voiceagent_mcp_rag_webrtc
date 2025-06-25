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

# telecom_agent/src/config.py
import os

# --- API Keys & Credentials (Set in Replit Secrets) ---
# For Gemini and Embeddings API
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

# --- MCP Server Configuration ---
# The URL where your mcp_server is running
MCP_SERVER_URL = os.environ.get('MCP_SERVER_URL') # e.g., http://localhost:8081
# A secret token to authenticate between the agent and the MCP server
MCP_AUTH_TOKEN = os.environ.get('MCP_AUTH_TOKEN')


# --- Knowledge Base and Indexing Configuration ---
KB_DOCUMENTS_PATH = "knowledge_base/documents"
KB_METADATA_PATH = "knowledge_base/metadata"
CHROMA_DB_PATH = "knowledge_base/embeddings"
WHOOSH_INDEX_PATH = "knowledge_base/indices"

# --- RAG and Model Configuration ---
EMBEDDING_MODEL = "models/text-embedding-004"
GENERATIVE_MODEL = "gemini-1.5-flash"
RRF_K = 20

# --- Chunking Configuration ---
CHUNK_SIZE = 768
CHUNK_OVERLAP = 100

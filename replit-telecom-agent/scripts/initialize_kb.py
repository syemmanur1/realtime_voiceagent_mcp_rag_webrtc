# scripts/initialize_kb.py
import os
import sys

# Add the 'src' directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from ingestion import run_ingestion

if __name__ == "__main__":
    print("Initializing Knowledge Base...")
    print("This will process documents, create embeddings, and build search indices.")
    run_ingestion()
    print("Knowledge Base initialization complete.")

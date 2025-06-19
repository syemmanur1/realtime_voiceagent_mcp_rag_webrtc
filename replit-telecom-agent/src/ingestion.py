# telecom_agent/src/ingestion.py
import os
import json
import google.generativeai as genai
import chromadb
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser

from config import (
    GOOGLE_API_KEY, KB_DOCUMENTS_PATH, KB_METADATA_PATH,
    CHROMA_DB_PATH, WHOOSH_INDEX_PATH, EMBEDDING_MODEL,
    CHUNK_SIZE, CHUNK_OVERLAP
)

# Configure the generative AI model
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

def intelligent_chunker(text, chunk_size, overlap):
    # This is a simplified chunker; a real implementation might use NLP libraries
    # to better preserve sentence boundaries.
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks

def run_ingestion():
    """
    Full pipeline to ingest documents: parse, chunk, embed, and index.
    """
    if not GOOGLE_API_KEY:
        print("ERROR: GOOGLE_API_KEY not found. Please set it in Replit Secrets.")
        return
        
    # 1. Setup Clients
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection_name = "telecom_kb"
    # Delete collection if it exists to ensure a fresh start
    if any(collection.name == collection_name for collection in chroma_client.list_collections()):
        chroma_client.delete_collection(name=collection_name)
    collection = chroma_client.create_collection(name=collection_name)

    # 2. Setup Whoosh index
    if not os.path.exists(WHOOSH_INDEX_PATH):
        os.makedirs(WHOOSH_INDEX_PATH)
    schema = Schema(id=ID(stored=True, unique=True), content=TEXT(stored=True))
    ix = create_in(WHOOSH_INDEX_PATH, schema)
    writer = ix.writer()

    # 3. Load Metadata
    metadata_map = {}
    for fname in os.listdir(KB_METADATA_PATH):
        if fname.endswith(".jsonl"):
            with open(os.path.join(KB_METADATA_PATH, fname), 'r') as f:
                for line in f:
                    meta = json.loads(line)
                    # --- FIX: Changed 'doc_id' to 'id' to match sample data ---
                    doc_id = meta.get('id') 
                    if doc_id:
                        metadata_map[doc_id] = meta

    # 4. Process and Embed Documents
    all_chunks = []
    doc_ids = []
    chunk_metadatas = []

    file_list = [f for f in os.listdir(KB_DOCUMENTS_PATH) if f.endswith('.txt')]
    print(f"Found {len(file_list)} documents to process.")

    for filename in file_list:
        doc_id = os.path.splitext(filename)[0]
        with open(os.path.join(KB_DOCUMENTS_PATH, filename), 'r') as f:
            content = f.read()
        
        chunks = intelligent_chunker(content, CHUNK_SIZE, CHUNK_OVERLAP)
        
        for i, chunk_text in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            doc_ids.append(chunk_id)
            all_chunks.append(chunk_text)
            
            parent_meta = metadata_map.get(doc_id, {})
            current_meta = parent_meta.copy()
            current_meta['source'] = filename
            chunk_metadatas.append(current_meta)
            writer.add_document(id=chunk_id, content=chunk_text)

    # 5. Generate Embeddings
    print(f"Generating embeddings for {len(all_chunks)} chunks...")
    embeddings = genai.embed_documents(model=EMBEDDING_MODEL, content=all_chunks)

    # 6. Add to ChromaDB
    collection.add(
        ids=doc_ids,
        embeddings=embeddings['embedding'],
        documents=all_chunks,
        metadatas=chunk_metadatas
    )

    # 7. Commit changes to Whoosh
    writer.commit()
    print("Ingestion complete. Vector DB and sparse index are ready.")

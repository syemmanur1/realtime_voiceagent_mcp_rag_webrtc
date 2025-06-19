# telecom_agent/src/rag_pipeline.py
import google.generativeai as genai
import chromadb
from whoosh.index import open_dir
from whoosh.qparser import QueryParser

from config import (
    GOOGLE_API_KEY, CHROMA_DB_PATH, WHOOSH_INDEX_PATH,
    EMBEDDING_MODEL, GENERATIVE_MODEL, RRF_K
)

# --- Initialize clients ---
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

def get_db_clients():
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = chroma_client.get_collection(name="telecom_kb")
    ix = open_dir(WHOOSH_INDEX_PATH)
    return collection, ix

def retrieve(query: str, n_results=10) -> dict:
    """
    Performs hybrid retrieval using dense (ChromaDB) and sparse (Whoosh) search.
    """
    collection, ix = get_db_clients()
    
    # 1. Dense Retrieval (Semantic Search)
    query_embedding = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=query,
        task_type="retrieval_query"
    )['embedding']
    
    dense_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )
    
    # 2. Sparse Retrieval (Keyword Search)
    with ix.searcher() as searcher:
        query_parser = QueryParser("content", ix.schema)
        parsed_query = query_parser.parse(query)
        sparse_results = searcher.search(parsed_query, limit=n_results)
        sparse_docs = [{"id": hit['id'], "score": hit.score} for hit in sparse_results]

    return {"dense": dense_results['ids'][0], "sparse": sparse_docs}

def reciprocal_rank_fusion(retrieval_results: dict, k=60) -> list:
    """
    Combines search results using Reciprocal Rank Fusion (RRF).
    """
    fused_scores = {}
    
    # Process dense results
    for i, doc_id in enumerate(retrieval_results.get("dense", [])):
        rank = i + 1
        if doc_id not in fused_scores:
            fused_scores[doc_id] = 0
        fused_scores[doc_id] += 1 / (k + rank)

    # Process sparse results
    for i, doc in enumerate(retrieval_results.get("sparse", [])):
        rank = i + 1
        doc_id = doc['id']
        if doc_id not in fused_scores:
            fused_scores[doc_id] = 0
        fused_scores[doc_id] += 1 / (k + rank)

    reranked_results = sorted(fused_scores.keys(), key=lambda id: fused_scores[id], reverse=True)
    return reranked_results

def generate_response(query: str, context: list, reranked_ids: list) -> str:
    """
    Generates a response using the Gemini model with retrieved context.
    """
    collection, _ = get_db_clients()
    
    # Fetch the content of the top documents
    top_docs_content = []
    if reranked_ids:
        retrieved_docs = collection.get(ids=reranked_ids, include=["documents"])
        top_docs_content = retrieved_docs.get('documents', [])

    context_str = "\n".join(top_docs_content)
    
    prompt_template = f"""
    You are a helpful and friendly telecom support agent. Your role is to assist users with network and device troubleshooting.
    Use the following retrieved knowledge base articles to answer the user's question.
    If the articles do not contain the answer, say that you don't have enough information but offer to help with other issues.
    Do not mention the knowledge base or the articles in your response. Just answer the question directly.

    Previous conversation:
    {context}
    
    Knowledge Base Articles:
    ---
    {context_str}
    ---

    User's Question: "{query}"

    Your Answer:
    """

    model = genai.GenerativeModel(GENERATIVE_MODEL)
    response = model.generate_content(prompt_template)
    
    return response.text

def agent_pipeline(query: str, conversation_history: list):
    """
    The main pipeline for the agentic RAG system.
    """
    # 1. Hybrid Retrieval
    retrieval_results = retrieve(query)
    
    # 2. Fusion/Reranking
    reranked_ids = reciprocal_rank_fusion(retrieval_results, k=RRF_K)[:5]
    
    # 3. Generate Response
    response_text = generate_response(query, conversation_history, reranked_ids)
    
    return response_text

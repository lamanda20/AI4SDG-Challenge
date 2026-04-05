"""
rag/retriever.py
Queries Pinecone vector DB and returns relevant medical guidelines.
Used by clinician_rag.py.
"""

import os
from typing import List

_model = None
_index = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model


def _get_index():
    global _index
    if _index is None:
        import pinecone as pc_module
        api_key = os.getenv("PINECONE_API_KEY")
        index_name = os.getenv("PINECONE_INDEX", "sportrx-guidelines")
        if not api_key:
            raise ValueError("PINECONE_API_KEY not set in .env")
        if hasattr(pc_module, 'Pinecone'):
            from pinecone import Pinecone
            pc = Pinecone(api_key=api_key)
            _index = pc.Index(index_name)
        else:
            pc_module.init(api_key=api_key, environment=os.getenv("PINECONE_ENV", "us-east-1-aws"))
            _index = pc_module.Index(index_name)
    return _index


def retrieve(query: str, top_k: int = 4) -> List[str]:
    """
    Embed query -> search Pinecone -> return top_k relevant text chunks.
    """
    model = _get_model()
    index = _get_index()

    # Embed the query
    query_vector = model.encode(query).tolist()

    # Search Pinecone
    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
    )

    # Extract text from results
    guidelines = []
    for match in results.get("matches", []):
        text = match.get("metadata", {}).get("text", "")
        source = match.get("metadata", {}).get("source", "")
        score = match.get("score", 0)
        if text and score > 0.3:   # filter low-relevance results
            guidelines.append(f"[{source}] {text}")

    return guidelines


def is_available() -> bool:
    """Check if Pinecone is configured and reachable."""
    try:
        if not os.getenv("PINECONE_API_KEY"):
            return False
        _get_index()
        return True
    except Exception:
        return False

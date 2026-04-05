"""
rag/indexer.py
Chunks documents, embeds with HuggingFace (free), uploads to Pinecone.
Run once to build the vector database.
"""

import os
import re
from typing import List, Dict

DOCS_DIR = os.path.join(os.path.dirname(__file__), "documents")
CHUNK_SIZE = 400      # characters per chunk
CHUNK_OVERLAP = 80    # overlap between chunks


# ── Text chunking ──────────────────────────────────────────────────────────────

def _load_documents() -> List[Dict]:
    """Load all .txt files from documents/ folder."""
    docs = []
    if not os.path.exists(DOCS_DIR):
        raise FileNotFoundError(f"Documents folder not found: {DOCS_DIR}. Run downloader.py first.")

    for fname in os.listdir(DOCS_DIR):
        if not fname.endswith(".txt"):
            continue
        path = os.path.join(DOCS_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().strip()
        if text:
            docs.append({"filename": fname, "text": text})

    print(f"  [OK] Loaded {len(docs)} documents")
    return docs


def _chunk_text(text: str, source: str) -> List[Dict]:
    """Split text into overlapping chunks."""
    # Clean text
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)

    chunks = []
    start = 0
    chunk_id = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end]

        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind(".")
            if last_period > CHUNK_SIZE // 2:
                chunk = chunk[:last_period + 1]
                end = start + last_period + 1

        chunk = chunk.strip()
        if len(chunk) > 50:  # skip tiny chunks
            chunks.append({
                "id": f"{source}_{chunk_id}",
                "text": chunk,
                "source": source,
            })
            chunk_id += 1

        start = end - CHUNK_OVERLAP

    return chunks


def chunk_all_documents() -> List[Dict]:
    """Load and chunk all documents."""
    docs = _load_documents()
    all_chunks = []
    for doc in docs:
        source = doc["filename"].replace(".txt", "")
        chunks = _chunk_text(doc["text"], source)
        all_chunks.extend(chunks)
    print(f"  [OK] Created {len(all_chunks)} chunks total")
    return all_chunks


# ── Embedding (HuggingFace - free) ────────────────────────────────────────────

def _get_embedder():
    """Load HuggingFace sentence transformer model."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        print("  [OK] Embedding model loaded (all-MiniLM-L6-v2)")
        return model
    except ImportError:
        raise ImportError("Run: pip install sentence-transformers")


def embed_chunks(chunks: List[Dict], model) -> List[Dict]:
    """Add embedding vectors to each chunk."""
    texts = [c["text"] for c in chunks]
    print(f"  Embedding {len(texts)} chunks...")
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)
    for i, chunk in enumerate(chunks):
        chunk["embedding"] = embeddings[i].tolist()
    print("  [OK] Embeddings computed")
    return chunks


# ── Pinecone upload ────────────────────────────────────────────────────────────

def _get_pinecone_index():
    """Connect to Pinecone and return index."""
    try:
        import pinecone as pc_module
        # Support both old and new Pinecone SDK
        if hasattr(pc_module, 'Pinecone'):
            from pinecone import Pinecone, ServerlessSpec
            pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
            index_name = os.getenv("PINECONE_INDEX", "sportrx-guidelines")
            existing = [i.name for i in pc.list_indexes()]
            if index_name not in existing:
                print(f"  Creating Pinecone index '{index_name}'...")
                pc.create_index(
                    name=index_name,
                    dimension=384,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )
                print(f"  [OK] Index '{index_name}' created")
            else:
                print(f"  [OK] Index '{index_name}' already exists")
            return pc.Index(index_name)
        else:
            # Old SDK (pinecone-client < 3.0)
            pc_module.init(
                api_key=os.getenv("PINECONE_API_KEY"),
                environment=os.getenv("PINECONE_ENV", "us-east-1-aws")
            )
            index_name = os.getenv("PINECONE_INDEX", "sportrx-guidelines")
            if index_name not in pc_module.list_indexes():
                print(f"  Creating Pinecone index '{index_name}'...")
                pc_module.create_index(index_name, dimension=384, metric="cosine")
                print(f"  [OK] Index '{index_name}' created")
            else:
                print(f"  [OK] Index '{index_name}' already exists")
            return pc_module.Index(index_name)
    except ImportError:
        raise ImportError("Run: pip install pinecone")


def upload_to_pinecone(chunks: List[Dict]):
    """Upload embedded chunks to Pinecone in batches."""
    index = _get_pinecone_index()

    # Prepare vectors
    vectors = [
        {
            "id": chunk["id"],
            "values": chunk["embedding"],
            "metadata": {
                "text": chunk["text"],
                "source": chunk["source"],
            },
        }
        for chunk in chunks
    ]

    # Upload in batches of 100
    batch_size = 100
    total = 0
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        index.upsert(vectors=batch)
        total += len(batch)
        print(f"  Uploaded {total}/{len(vectors)} vectors...")

    print(f"  [OK] All {total} vectors uploaded to Pinecone")


# ── Main ───────────────────────────────────────────────────────────────────────

def build_index():
    """Full indexing pipeline: load -> chunk -> embed -> upload."""
    from dotenv import load_dotenv
    load_dotenv()

    print("\n[1/3] Loading and chunking documents...")
    chunks = chunk_all_documents()

    print("\n[2/3] Computing embeddings (HuggingFace)...")
    model = _get_embedder()
    chunks = embed_chunks(chunks, model)

    print("\n[3/3] Uploading to Pinecone...")
    upload_to_pinecone(chunks)

    print("\n[DONE] Vector database is ready!")
    print(f"  Index: {os.getenv('PINECONE_INDEX', 'sportrx-guidelines')}")
    print(f"  Total vectors: {len(chunks)}")


if __name__ == "__main__":
    build_index()

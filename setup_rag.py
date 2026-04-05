"""
setup_rag.py
One command to build the full RAG pipeline:
  1. Install dependencies
  2. Download medical documents (PubMed + static guidelines)
  3. Chunk + embed + upload to Pinecone
  4. Test a sample query

Usage:
  python setup_rag.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


def check_env():
    print("[1/4] Checking environment...")
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("""
  [ERROR] PINECONE_API_KEY not found in .env

  Steps to get your free key:
  1. Go to https://pinecone.io
  2. Sign up (free, no credit card)
  3. Go to API Keys -> Create API Key
  4. Add to your .env file:
       PINECONE_API_KEY=your-key-here
       PINECONE_INDEX=sportrx-guidelines
  5. Run this script again
""")
        sys.exit(1)
    print(f"  [OK] PINECONE_API_KEY found")
    print(f"  [OK] PINECONE_INDEX = {os.getenv('PINECONE_INDEX', 'sportrx-guidelines')}")


def install_deps():
    print("\n[2/4] Installing RAG dependencies...")
    import subprocess
    packages = ["sentence-transformers", "pinecone"]
    for pkg in packages:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg, "-q"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"  [OK] {pkg}")
        else:
            print(f"  [WARN] {pkg} install issue: {result.stderr[:100]}")


def download_docs():
    print("\n[3/4] Downloading medical documents...")
    from rag.downloader import download_documents
    count = download_documents()
    if count == 0:
        print("  [ERROR] No documents downloaded")
        sys.exit(1)


def build_index():
    print("\n[4/4] Building vector index...")
    from rag.indexer import build_index
    build_index()


def test_query():
    print("\n[TEST] Testing a sample query...")
    from rag.retriever import retrieve
    query = "exercise guidelines for diabetic hypertensive patient moderate risk weight loss"
    results = retrieve(query, top_k=3)
    if results:
        print(f"  [OK] Retrieved {len(results)} guidelines:")
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r[:100]}...")
    else:
        print("  [WARN] No results returned - check your Pinecone index")


if __name__ == "__main__":
    print("="*60)
    print("  SPORTRX AI - RAG SETUP")
    print("="*60)

    check_env()
    install_deps()
    download_docs()
    build_index()
    test_query()

    print("\n" + "="*60)
    print("  RAG SETUP COMPLETE")
    print("  Your pipeline now uses real medical guidelines!")
    print("="*60 + "\n")

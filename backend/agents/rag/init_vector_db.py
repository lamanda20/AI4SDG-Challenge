#!/usr/bin/env python
"""
Initialize Vector DB with PDFs and Medical Guidelines

This script loads PDF documents from the documents folder and stores their 
embeddings in Chroma vector database for use by SOUFIA (Prescriber Agent).

Workflow:
1. Scan data/documents/ for PDF files
2. Extract text from PDFs using pypdf
3. Generate embeddings using Nomic or configured provider
4. Store embeddings in Chroma with metadata
5. Verify storage and report statistics

Usage:
    python init_vector_db.py
    python init_vector_db.py --clear  # Clear existing DB first
    python init_vector_db.py --verbose  # Detailed logging
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Any
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def initialize_vector_db(
    pdf_dir: Path = Path("backend/agents/rag/data/documents"),
    clear_existing: bool = False,
    verbose: bool = False,
):
    """
    Initialize vector database with PDFs and medical guidelines.
    
    Args:
        pdf_dir: Directory containing PDF files
        clear_existing: Clear existing database before loading
        verbose: Enable verbose logging
    """
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("=" * 80)
    logger.info("VECTOR DATABASE INITIALIZATION")
    logger.info("=" * 80)
    logger.info(f"PDF Directory: {pdf_dir}")
    logger.info(f"Clear Existing: {clear_existing}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    # Import RAG components
    try:
        from backend.agents.rag.config import rag_config
        from backend.agents.rag.document_loader import create_document_loader
        from backend.agents.rag.embeddings import create_embedding_provider
        from backend.agents.rag.vector_store import create_vector_store
        logger.info("✓ Imported RAG components")
    except ImportError as e:
        logger.error(f"Failed to import RAG components: {e}")
        return False
    
    # Verify PDF directory
    if not pdf_dir.exists():
        logger.error(f"PDF directory does not exist: {pdf_dir}")
        return False
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF files")
    for pdf_file in pdf_files:
        logger.info(f"  - {pdf_file.name}")
    
    if not pdf_files:
        logger.warning("No PDF files found in directory")
        return False
    
    try:
        # Step 1: Initialize embeddings provider
        logger.info("\n[STEP 1] Initializing embeddings provider...")
        embeddings_provider = create_embedding_provider(
            provider=rag_config.embedding_provider,
            model=rag_config.embedding_model,
        )
        logger.info(f"✓ Embeddings provider: {rag_config.embedding_provider}")
        logger.info(f"  Model: {rag_config.embedding_model}")
        logger.info(f"  Dimension: {rag_config.embedding_dimension}")
        
        # Step 2: Initialize vector store
        logger.info("\n[STEP 2] Initializing vector store...")
        
        if rag_config.vector_db_type.lower() == "pinecone":
            logger.info("Using Pinecone (cloud-managed vector DB)")
            vector_store = create_vector_store(
                store_type="pinecone",
                api_key=rag_config.pinecone_api_key,
                environment=rag_config.pinecone_environment,
                index_name=rag_config.pinecone_index_name,
                namespace=rag_config.pinecone_namespace,
                embedding_dim=rag_config.embedding_dimension,
            )
            logger.info(f"✓ Vector store: Pinecone")
            logger.info(f"  Index: {rag_config.pinecone_index_name}")
            logger.info(f"  Environment: {rag_config.pinecone_environment}")
            logger.info(f"  Namespace: {rag_config.pinecone_namespace}")
            
        elif rag_config.vector_db_type.lower() == "chroma":
            logger.info("Using Chroma (local vector DB)")
            if clear_existing and rag_config.chroma_persist_dir.exists():
                logger.info(f"Clearing existing database at {rag_config.chroma_persist_dir}")
                import shutil
                shutil.rmtree(rag_config.chroma_persist_dir)
            
            vector_store = create_vector_store(
                store_type="chroma",
                collection_name=rag_config.chroma_collection_name,
                persist_dir=rag_config.chroma_persist_dir,
            )
            logger.info(f"✓ Vector store: Chroma")
            logger.info(f"  Collection: {rag_config.chroma_collection_name}")
            logger.info(f"  Persist dir: {rag_config.chroma_persist_dir}")
        
        else:
            raise ValueError(f"Unsupported vector DB type: {rag_config.vector_db_type}")
        
        # Step 3: Load PDF documents
        logger.info("\n[STEP 3] Loading PDF documents...")
        pdf_loader = create_document_loader(
            loader_type="pdf",
            pdf_dir=pdf_dir,
        )
        documents = pdf_loader.load()
        
        if not documents:
            logger.error("No documents loaded from PDFs")
            return False
        
        logger.info(f"✓ Loaded {len(documents)} documents from PDFs")
        for i, doc in enumerate(documents, 1):
            logger.debug(f"  {i}. {doc.title} ({len(doc.content)} chars)")
        
        # Step 4: Generate embeddings and store
        logger.info("\n[STEP 4] Generating embeddings and storing in vector DB...")
        logger.info(f"Batch size: {rag_config.batch_size_embeddings}")
        
        vector_store.add_documents(documents, embeddings_provider)
        logger.info(f"✓ Added {len(documents)} documents to vector store")
        
        # Step 5: Verify storage
        logger.info("\n[STEP 5] Verifying storage...")
        store_size = vector_store.get_size()
        logger.info(f"✓ Vector store contains {store_size} documents")
        
        if store_size == 0:
            logger.error("Vector store appears to be empty!")
            return False
        
        # Step 6: Generate report
        logger.info("\n[STEP 6] Generating initialization report...")
        report = {
            "timestamp": datetime.now().isoformat(),
            "vector_db_type": rag_config.vector_db_type,
            "embedding_provider": rag_config.embedding_provider,
            "embedding_model": rag_config.embedding_model,
            "embedding_dimension": rag_config.embedding_dimension,
            "total_documents": store_size,
            "documents": [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "source": doc.source,
                    "content_length": len(doc.content),
                }
                for doc in documents
            ],
            "status": "SUCCESS",
        }
        
        if rag_config.vector_db_type.lower() == "pinecone":
            report["pinecone_index"] = rag_config.pinecone_index_name
            report["pinecone_namespace"] = rag_config.pinecone_namespace
            report["pinecone_environment"] = rag_config.pinecone_environment
            report_path = Path(f"{rag_config.pinecone_index_name}_initialization_report.json")
        else:
            report_path = rag_config.chroma_persist_dir / "initialization_report.json"
        
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"✓ Report saved to {report_path}")
        
        # Final summary
        logger.info("\n" + "=" * 80)
        logger.info("INITIALIZATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info(f"✓ Vector DB initialized with {store_size} documents")
        logger.info(f"✓ Ready for SOUFIA (Prescriber Agent) to use")
        
        if rag_config.vector_db_type.lower() == "pinecone":
            logger.info(f"\nPinecone Details:")
            logger.info(f"  Index: {rag_config.pinecone_index_name}")
            logger.info(f"  Namespace: {rag_config.pinecone_namespace}")
            logger.info(f"  Status: Cloud-managed (auto-scaling)")
        
        logger.info(f"\nNext steps:")
        logger.info(f"1. Configure .env with vector DB settings")
        logger.info(f"2. Start the RAG pipeline")
        logger.info(f"3. Query with patient data")
        logger.info(f"4. SOUFIA will generate personalized training plans")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during initialization: {e}", exc_info=True)
        return False


def verify_vector_db(persist_dir: Path = None) -> Dict[str, Any]:
    """
    Verify an existing vector database.
    
    Args:
        persist_dir: Path to Chroma persistence directory
        
    Returns:
        Dictionary with verification results
    """
    
    from backend.agents.rag.config import rag_config
    from backend.agents.rag.vector_store import create_vector_store
    
    if persist_dir is None:
        persist_dir = rag_config.chroma_persist_dir
    
    logger.info(f"\nVERIFYING VECTOR DB at {persist_dir}")
    
    try:
        vector_store = create_vector_store(
            store_type="chroma",
            collection_name=rag_config.chroma_collection_name,
            persist_dir=persist_dir,
        )
        vector_store.load(persist_dir)
        
        size = vector_store.get_size()
        
        report = {
            "path": str(persist_dir),
            "exists": True,
            "document_count": size,
            "status": "READY" if size > 0 else "EMPTY",
        }
        
        logger.info(f"✓ Vector DB verified: {size} documents")
        return report
        
    except Exception as e:
        logger.error(f"✗ Verification failed: {e}")
        return {"path": str(persist_dir), "exists": False, "error": str(e)}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Initialize Vector Database with Medical PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard initialization
  python init_vector_db.py
  
  # Clear existing database first
  python init_vector_db.py --clear
  
  # Verbose output
  python init_vector_db.py --verbose
  
  # Verify existing database
  python init_vector_db.py --verify
        """,
    )
    
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing vector database before loading",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify existing database without loading",
    )
    parser.add_argument(
        "--pdf-dir",
        type=Path,
        default=Path("backend/agents/rag/data/documents"),
        help="Directory containing PDF files",
    )
    
    args = parser.parse_args()
    
    if args.verify:
        result = verify_vector_db()
        print(json.dumps(result, indent=2))
        sys.exit(0)
    
    success = initialize_vector_db(
        pdf_dir=args.pdf_dir,
        clear_existing=args.clear,
        verbose=args.verbose,
    )
    
    sys.exit(0 if success else 1)

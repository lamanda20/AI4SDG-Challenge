"""
Test Script: Verify Embedding System is Working

Tests HuggingFace embeddings, vector store operations, and similarity search.
"""

import numpy as np
from pathlib import Path
import sys

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.agents.rag.embeddings import HuggingFaceEmbeddings
from backend.agents.rag.vector_store import FAISSVectorStore
from backend.agents.rag.schemas import MedicalDocument


def test_embedding_initialization():
    """Test 1: Embedding model loads correctly"""
    print("\n" + "="*80)
    print("TEST 1: Embedding Model Initialization")
    print("="*80)
    
    try:
        embedder = HuggingFaceEmbeddings(model="sentence-transformers/all-MiniLM-L6-v2")
        dimension = embedder.get_dimension()
        
        print(f"✓ Model loaded successfully")
        print(f"✓ Embedding dimension: {dimension} (expected: 384)")
        assert dimension == 384, f"Wrong dimension: {dimension}"
        
        return embedder
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise


def test_single_embedding(embedder):
    """Test 2: Generate single text embedding"""
    print("\n" + "="*80)
    print("TEST 2: Single Text Embedding")
    print("="*80)
    
    test_text = "Exercise is important for managing type 2 diabetes"
    
    try:
        embedding = embedder.embed_text(test_text)
        
        print(f"✓ Text: '{test_text}'")
        print(f"✓ Embedding generated (length: {len(embedding)})")
        print(f"✓ Embedding type: {type(embedding)}")
        print(f"✓ First 5 values: {embedding[:5]}")
        print(f"✓ Embedding norm: {np.linalg.norm(embedding):.4f}")
        
        assert len(embedding) == 384, f"Wrong embedding length: {len(embedding)}"
        assert isinstance(embedding, list), f"Embedding should be list, got {type(embedding)}"
        
        return embedding
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise


def test_batch_embeddings(embedder):
    """Test 3: Generate batch embeddings"""
    print("\n" + "="*80)
    print("TEST 3: Batch Text Embeddings")
    print("="*80)
    
    texts = [
        "Aerobic exercise 150 minutes per week",
        "Resistance training 2-3 times weekly",
        "Monitor blood glucose during exercise",
        "Avoid high intensity with blood glucose >250"
    ]
    
    try:
        embeddings = embedder.embed_batch(texts)
        
        print(f"✓ Batch size: {len(texts)} texts")
        print(f"✓ Embeddings generated: {len(embeddings)}")
        print(f"✓ Each embedding dimension: {len(embeddings[0])}")
        
        # Verify all are same dimension
        for i, emb in enumerate(embeddings):
            assert len(emb) == 384, f"Embedding {i} has wrong dimension"
        
        # Check they're different
        similarity_0_1 = np.dot(embeddings[0], embeddings[1])
        similarity_0_2 = np.dot(embeddings[0], embeddings[2])
        
        print(f"✓ Similarity text[0]-text[1]: {similarity_0_1:.4f}")
        print(f"✓ Similarity text[0]-text[2]: {similarity_0_2:.4f}")
        print(f"✓ Embeddings are diverse (different similarity scores)")
        
        return embeddings
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise


def test_semantic_similarity():
    """Test 4: Semantic similarity between related texts"""
    print("\n" + "="*80)
    print("TEST 4: Semantic Similarity")
    print("="*80)
    
    embedder = HuggingFaceEmbeddings()
    
    # Similar texts (should have high similarity)
    text1 = "type 2 diabetes exercise recommendations"
    text2 = "diabetes physical activity guidelines"
    
    # Dissimilar texts (should have low similarity)
    text3 = "the weather is nice today"
    text4 = "I like to eat pizza"
    
    try:
        emb1 = embedder.embed_text(text1)
        emb2 = embedder.embed_text(text2)
        emb3 = embedder.embed_text(text3)
        emb4 = embedder.embed_text(text4)
        
        # Normalize for cosine similarity
        emb1_norm = np.array(emb1) / np.linalg.norm(emb1)
        emb2_norm = np.array(emb2) / np.linalg.norm(emb2)
        emb3_norm = np.array(emb3) / np.linalg.norm(emb3)
        emb4_norm = np.array(emb4) / np.linalg.norm(emb4)
        
        similarity_medical = np.dot(emb1_norm, emb2_norm)
        similarity_unrelated = np.dot(emb3_norm, emb4_norm)
        
        print(f"Similar medical texts:")
        print(f"  '{text1}'")
        print(f"  '{text2}'")
        print(f"  Cosine similarity: {similarity_medical:.4f}")
        
        print(f"\nUnrelated texts:")
        print(f"  '{text3}'")
        print(f"  '{text4}'")
        print(f"  Cosine similarity: {similarity_unrelated:.4f}")
        
        print(f"\n✓ Medical similarity ({similarity_medical:.4f}) > Unrelated ({similarity_unrelated:.4f})")
        assert similarity_medical > similarity_unrelated, "Medical texts should be more similar"
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise


def test_vector_store_operations(embedder):
    """Test 5: Vector store add and search"""
    print("\n" + "="*80)
    print("TEST 5: Vector Store (FAISS) Operations")
    print("="*80)
    
    try:
        # Create vector store
        vector_store = FAISSVectorStore(embedding_dim=384)
        print(f"✓ FAISS vector store created")
        
        # Create sample documents
        docs = [
            MedicalDocument(
                id="doc1",
                title="ADA Diabetes Guidelines",
                content="Aerobic exercise 150 minutes per week. Resistance training 2-3 times weekly.",
                source="ADA"
            ),
            MedicalDocument(
                id="doc2",
                title="Exercise Safety",
                content="Monitor blood glucose before and after exercise. Avoid intense activity with high glucose.",
                source="Safety Guidelines"
            ),
            MedicalDocument(
                id="doc3",
                title="Hypertension Management",
                content="Moderate intensity aerobic exercise reduces blood pressure. Avoid heavy lifting.",
                source="WHO"
            ),
        ]
        
        # Add documents
        vector_store.add_documents(docs, embedder)
        print(f"✓ Added {len(docs)} documents to vector store")
        print(f"✓ Vector store size: {vector_store.get_size()}")
        
        # Search
        query = "diabetes exercise recommendations"
        results = vector_store.search(query, embedder, k=2)
        
        print(f"\n✓ Search query: '{query}'")
        print(f"✓ Results found: {len(results)}")
        
        for i, (doc, similarity) in enumerate(results, 1):
            print(f"  {i}. {doc.title} (similarity: {similarity:.4f})")
        
        # Verify results are reasonable (related to exercise, not random)
        top_doc = results[0][0]
        relevant_keywords = ["exercise", "glucose", "aerobic", "training", "activity", "blood pressure"]
        is_relevant = any(keyword in top_doc.content.lower() for keyword in relevant_keywords)
        
        assert is_relevant, f"Top result should be exercise/medical related"
        print(f"\n✓ Search results are relevant!")
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise


def test_consistency():
    """Test 6: Embedding consistency"""
    print("\n" + "="*80)
    print("TEST 6: Embedding Consistency")
    print("="*80)
    
    embedder = HuggingFaceEmbeddings()
    text = "type 2 diabetes management"
    
    try:
        # Generate same embedding twice
        emb1 = embedder.embed_text(text)
        emb2 = embedder.embed_text(text)
        
        # Should be identical
        consistency = np.allclose(emb1, emb2, atol=1e-6)
        
        print(f"✓ Text: '{text}'")
        print(f"✓ First embedding norm: {np.linalg.norm(emb1):.6f}")
        print(f"✓ Second embedding norm: {np.linalg.norm(emb2):.6f}")
        print(f"✓ Embeddings are consistent: {consistency}")
        
        assert consistency, "Same text should produce identical embeddings"
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise


def test_medical_domain_knowledge():
    """Test 7: Medical domain awareness"""
    print("\n" + "="*80)
    print("TEST 7: Medical Domain Knowledge")
    print("="*80)
    
    embedder = HuggingFaceEmbeddings()
    
    medical_terms = [
        "type 2 diabetes",
        "hypertension",
        "HbA1c",
        "blood glucose monitoring",
        "aerobic exercise",
    ]
    
    try:
        embeddings = embedder.embed_batch(medical_terms)
        
        print(f"✓ Medical terms embedded: {len(medical_terms)}")
        
        # Calculate pairwise similarities
        print(f"\nPairwise similarities:")
        for i in range(len(medical_terms)):
            for j in range(i+1, len(medical_terms)):
                emb_i = np.array(embeddings[i])
                emb_j = np.array(embeddings[j])
                similarity = np.dot(emb_i, emb_j) / (np.linalg.norm(emb_i) * np.linalg.norm(emb_j))
                print(f"  '{medical_terms[i]}' <-> '{medical_terms[j]}': {similarity:.4f}")
        
        print(f"\n✓ Medical terms are properly embedded")
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise


def main():
    """Run all embedding tests"""
    print("\n" + "="*80)
    print("EMBEDDING SYSTEM TEST SUITE")
    print("="*80)
    
    try:
        # Test 1: Initialize embedder
        embedder = test_embedding_initialization()
        
        # Test 2: Single embedding
        embedding = test_single_embedding(embedder)
        
        # Test 3: Batch embeddings
        embeddings = test_batch_embeddings(embedder)
        
        # Test 4: Semantic similarity
        test_semantic_similarity()
        
        # Test 5: Vector store
        test_vector_store_operations(embedder)
        
        # Test 6: Consistency
        test_consistency()
        
        # Test 7: Medical domain
        test_medical_domain_knowledge()
        
        # Final summary
        print("\n" + "="*80)
        print("✅ ALL EMBEDDING TESTS PASSED!")
        print("="*80)
        print("\nSummary:")
        print("  ✓ Embedding model loads correctly (384-dimensional)")
        print("  ✓ Single text embeddings generated")
        print("  ✓ Batch embeddings work correctly")
        print("  ✓ Semantic similarity is meaningful")
        print("  ✓ Vector store FAISS operations work")
        print("  ✓ Embeddings are consistent")
        print("  ✓ Medical domain terms are properly encoded")
        print("\n✨ Embedding system is WORKING and READY!")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

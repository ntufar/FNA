#!/usr/bin/env python3
"""Test script for sentence-transformers embedding functionality.

This script tests the sentence-transformers installation and embedding
generation capabilities as specified in research.md.
"""

import sys
import numpy as np
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from services.embedding_service import EmbeddingService, EmbeddingServiceError


def test_embedding_installation():
    """Test if sentence-transformers is properly installed."""
    print("🧪 Testing Sentence Transformers Installation")
    print("=" * 50)
    
    try:
        service = EmbeddingService()
        print("✅ sentence-transformers library imported successfully")
        return True
        
    except ImportError as e:
        print(f"❌ sentence-transformers library not found: {e}")
        print("💡 Install with: pip install sentence-transformers")
        return False
    except Exception as e:
        print(f"❌ Embedding service initialization error: {e}")
        return False


def test_model_loading():
    """Test loading the MiniLM-L6-v2 model."""
    print("\n🔄 Testing Model Loading")
    print("=" * 35)
    
    try:
        service = EmbeddingService()
        
        print("Loading all-MiniLM-L6-v2 model (this may take a moment)...")
        success = service.load_model()
        
        if success:
            info = service.get_model_info()
            print("✅ Model loaded successfully")
            print(f"Model: {info['model_name']}")
            print(f"Dimension: {info['embedding_dimension']}")
            print(f"Device: {info['device']}")
            return True
        else:
            print("❌ Model loading failed")
            return False
            
    except Exception as e:
        print(f"❌ Model loading error: {e}")
        return False


def test_embedding_generation():
    """Test generating embeddings for sample financial text."""
    print("\n🎯 Testing Embedding Generation")
    print("=" * 40)
    
    try:
        service = EmbeddingService()
        
        if not service.is_loaded():
            service.load_model()
        
        # Sample financial texts for testing
        sample_texts = [
            "The company reported strong quarterly earnings with revenue growth of 15%.",
            "Management expressed concerns about rising costs and market volatility.",
            "Our outlook for the next quarter remains positive despite challenges.",
            "The financial performance exceeded analyst expectations significantly."
        ]
        
        print(f"Generating embeddings for {len(sample_texts)} sample texts...")
        
        # Generate embeddings
        embeddings = service.encode_texts(sample_texts)
        
        print(f"✅ Embeddings generated successfully")
        print(f"Shape: {embeddings.shape}")
        print(f"Data type: {embeddings.dtype}")
        
        # Test similarity computation
        query = "Quarterly financial results show strong performance"
        results = service.find_most_similar(query, sample_texts, top_k=2)
        
        print(f"\n🔍 Similarity Search Results for: '{query}'")
        for i, result in enumerate(results):
            print(f"{i+1}. Similarity: {result['similarity']:.3f}")
            print(f"   Text: {result['text'][:60]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding generation error: {e}")
        return False


def main():
    """Run all embedding tests."""
    print("🏗️ FNA Sentence Transformers Embedding Test Suite")
    print("=" * 60)
    
    # Test installation
    installation_ok = test_embedding_installation()
    
    if not installation_ok:
        print("\n❌ Installation test failed!")
        print("Please install sentence-transformers before proceeding:")
        print("  pip install sentence-transformers")
        sys.exit(1)
    
    # Test model loading
    loading_ok = test_model_loading()
    
    if not loading_ok:
        print("\n❌ Model loading test failed!")
        sys.exit(1)
    
    # Test embedding generation
    generation_ok = test_embedding_generation()
    
    if installation_ok and loading_ok and generation_ok:
        print("\n🎉 All embedding tests passed!")
        print("\nEmbedding service is ready for:")
        print("• Financial text similarity search")
        print("• Narrative section embeddings")
        print("• Vector database integration")
    else:
        print("\n⚠️ Some tests failed - check configuration")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Test script for LM Studio API connectivity and model functionality.

This script tests the connection to LM Studio server running qwen/qwen3-4b-2507
and verifies basic text generation capabilities.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from core.model_config import Qwen3ModelManager, ModelSettings, LMStudioAPIError


def test_lm_studio_connection():
    """Test connection to LM Studio server."""
    print("🔌 Testing LM Studio Connection")
    print("=" * 40)
    
    try:
        manager = Qwen3ModelManager()
        
        # Test connection
        success = manager.check_connection()
        
        if success:
            print("✅ Successfully connected to LM Studio")
            
            # Get available models
            try:
                models = manager.get_available_models()
                print(f"Available models: {len(models)}")
                for model in models:
                    print(f"  - {model.get('id', 'Unknown')}")
            except Exception as e:
                print(f"⚠️ Could not get model list: {e}")
            
            return True
        else:
            print("❌ Failed to connect to LM Studio")
            return False
            
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        return False


def test_text_generation():
    """Test text generation with sample financial prompts."""
    print("\n🤖 Testing Text Generation")
    print("=" * 35)
    
    try:
        manager = Qwen3ModelManager()
        
        if not manager.is_loaded():
            if not manager.load_model():
                print("❌ Cannot connect to LM Studio for testing")
                return False
        
        # Test prompts for financial analysis
        test_prompts = [
            "Analyze the sentiment of this financial text: 'The company reported record quarterly earnings, exceeding analyst expectations by 15%.'",
            "What is the tone of this statement: 'Management expressed concerns about rising operational costs and market volatility.'",
            "Classify the sentiment: 'We remain optimistic about our growth prospects despite current challenges.'"
        ]
        
        print("Testing with financial sentiment analysis prompts...")
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n📝 Test {i}: {prompt[:50]}...")
            
            try:
                response = manager.generate_response(
                    prompt,
                    max_tokens=100,
                    temperature=0.1
                )
                
                print(f"✅ Response: {response[:150]}...")
                
            except LMStudioAPIError as e:
                print(f"❌ Generation failed: {e}")
                return False
        
        print("\n✅ All text generation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Text generation error: {e}")
        return False


def test_model_configuration():
    """Test model configuration and settings."""
    print("\n⚙️ Testing Model Configuration")
    print("=" * 40)
    
    try:
        manager = Qwen3ModelManager()
        
        # Get model info
        info = manager.get_model_info()
        
        print("Model Configuration:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        print("✅ Configuration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test error: {e}")
        return False


def main():
    """Run all LM Studio tests."""
    print("🏗️ FNA LM Studio API Test Suite")
    print("=" * 50)
    
    # Test connection
    connection_ok = test_lm_studio_connection()
    
    if not connection_ok:
        print("\n❌ LM Studio connection failed!")
        print("\nTroubleshooting:")
        print("1. Make sure LM Studio is running")
        print("2. Load the qwen/qwen3-4b-2507 model in LM Studio")
        print("3. Verify the server is running on http://127.0.0.1:1234")
        print("4. Check that the model is not currently loading")
        sys.exit(1)
    
    # Test configuration
    config_ok = test_model_configuration()
    
    # Test text generation
    generation_ok = test_text_generation()
    
    if connection_ok and config_ok and generation_ok:
        print("\n🎉 All LM Studio tests passed!")
        print("\nLM Studio integration is ready for:")
        print("• Financial narrative sentiment analysis")
        print("• Multi-dimensional tone classification")
        print("• Automated report analysis")
    else:
        print("\n⚠️ Some tests failed - check LM Studio configuration")
        sys.exit(1)


if __name__ == "__main__":
    main()

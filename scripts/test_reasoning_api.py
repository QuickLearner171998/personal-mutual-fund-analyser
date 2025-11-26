"""
Test script for Responses API integration with GPT-5 reasoning models
Tests different reasoning efforts and measures latency
"""
import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent))

from llm.llm_wrapper import invoke_llm
from utils.logger import get_logger
import config

logger = get_logger(__name__)

def test_reasoning_efforts():
    """Test different reasoning effort levels and measure latency"""
    
    test_query = {
        "role": "user",
        "content": "Analyze this portfolio strategy: 90% equity, 10% debt. Should I rebalance?"
    }
    
    efforts = ["low", "medium", "high"]
    
    print("="*80)
    print("TESTING REASONING API WITH DIFFERENT EFFORTS")
    print("="*80)
    
    for effort in efforts:
        print(f"\n{'='*80}")
        print(f"Testing with reasoning_effort = '{effort}'")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        try:
            response = invoke_llm(
                messages=[test_query],
                use_reasoning=True,
                reasoning_effort=effort,
                stream=False
            )
            
            elapsed = time.time() - start_time
            
            print(f"\n✅ SUCCESS")
            print(f"⏱️  Latency: {elapsed:.2f} seconds")
            print(f"📝 Response length: {len(response)} characters")
            print(f"📄 Response preview: {response[:200]}...")
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\n❌ FAILED after {elapsed:.2f}s")
            print(f"Error: {str(e)}")

def test_intent_classification():
    """Test fast intent classification model"""
    
    print("\n" + "="*80)
    print("TESTING INTENT CLASSIFICATION (Fast Model)")
    print("="*80)
    
    test_query = {
        "role": "user",
        "content": "What is my portfolio value?"
    }
    
    start_time = time.time()
    
    try:
        response = invoke_llm(
            messages=[test_query],
            use_intent=True,
            stream=False
        )
        
        elapsed = time.time() - start_time
        
        print(f"\n✅ SUCCESS")
        print(f"⏱️  Latency: {elapsed:.2f} seconds")
        print(f"📝 Response: {response}")
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ FAILED after {elapsed:.2f}s")
        print(f"Error: {str(e)}")

def test_primary_model():
    """Test primary model for general queries"""
    
    print("\n" + "="*80)
    print("TESTING PRIMARY MODEL (General Queries)")
    print("="*80)
    
    test_query = {
        "role": "user",
        "content": "Explain XIRR in simple terms"
    }
    
    start_time = time.time()
    
    try:
        response = invoke_llm(
            messages=[test_query],
            use_reasoning=False,
            stream=False
        )
        
        elapsed = time.time() - start_time
        
        print(f"\n✅ SUCCESS")
        print(f"⏱️  Latency: {elapsed:.2f} seconds")
        print(f"📝 Response length: {len(response)} characters")
        print(f"📄 Response preview: {response[:200]}...")
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ FAILED after {elapsed:.2f}s")
        print(f"Error: {str(e)}")

def print_configuration():
    """Print current configuration"""
    
    print("\n" + "="*80)
    print("CURRENT CONFIGURATION")
    print("="*80)
    
    print(f"\n🔧 Model Configuration:")
    print(f"  - Primary Model: {config.PRIMARY_LLM_MODEL}")
    print(f"  - Reasoning Model: {config.REASONING_LLM_MODEL}")
    print(f"  - Intent Model: {config.INTENT_CLASSIFICATION_MODEL}")
    print(f"  - RAG Model: {config.RAG_LLM_MODEL}")
    print(f"  - Fallback Model: {config.FALLBACK_LLM_MODEL}")
    
    print(f"\n⚡ Latency Optimization:")
    print(f"  - Default Reasoning Effort: {config.REASONING_EFFORT_DEFAULT}")
    print(f"  - Max Tokens (Reasoning): {config.MAX_COMPLETION_TOKENS_REASONING}")
    print(f"  - Max Tokens (Primary): {config.MAX_COMPLETION_TOKENS_PRIMARY}")
    print(f"  - Reasoning Timeout: {config.REASONING_TIMEOUT}s")
    print(f"  - Primary Timeout: {config.PRIMARY_TIMEOUT}s")
    print(f"  - Prompt Caching: {'✅ Enabled' if config.ENABLE_PROMPT_CACHING else '❌ Disabled'}")
    print(f"  - Include Reasoning: {'✅ Yes (Debug)' if config.INCLUDE_REASONING else '❌ No (Production)'}")

if __name__ == "__main__":
    print("\n" + "🚀 "*40)
    print("GPT-5 RESPONSES API TEST SUITE")
    print("🚀 "*40)
    
    # Print configuration
    print_configuration()
    
    # Run tests
    print("\n\n" + "🧪 "*40)
    print("RUNNING TESTS")
    print("🧪 "*40)
    
    # Test 1: Intent Classification (fastest)
    test_intent_classification()
    
    # Test 2: Primary Model (fast)
    test_primary_model()
    
    # Test 3: Reasoning with different efforts (slow to slower)
    # Note: Uncomment to test, but be aware of API costs
    # test_reasoning_efforts()
    
    print("\n" + "="*80)
    print("✅ TEST SUITE COMPLETED")
    print("="*80)
    print("\nNote: Reasoning effort tests are commented out to avoid API costs.")
    print("Uncomment test_reasoning_efforts() in main to run full test suite.")

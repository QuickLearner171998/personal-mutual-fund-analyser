#!/usr/bin/env python3
"""
Isolated GPT-5-mini benchmark
Tests ONLY gpt-5-mini performance with current configuration
"""
import time
from llm.llm_wrapper import invoke_llm
from utils.logger import get_logger
import config

logger = get_logger(__name__)

def test_simple_query():
    """Test with a simple query"""
    print("\n" + "="*80)
    print("TEST 1: Simple Query (should be <2s)")
    print("="*80)
    
    messages = [
        {"role": "user", "content": "What is XIRR?"}
    ]
    
    start = time.time()
    response = invoke_llm(messages, use_reasoning=False, stream=False)
    elapsed = time.time() - start
    
    print(f"⏱️  Latency: {elapsed:.2f}s")
    print(f"📝 Response: {response[:200]}...")
    print(f"✅ Status: {'GOOD' if elapsed < 2 else 'SLOW'}")
    return elapsed

def test_medium_query():
    """Test with a medium complexity query"""
    print("\n" + "="*80)
    print("TEST 2: Medium Query (should be <5s)")
    print("="*80)
    
    messages = [
        {"role": "user", "content": "Explain portfolio rebalancing and when I should do it."}
    ]
    
    start = time.time()
    response = invoke_llm(messages, use_reasoning=False, stream=False)
    elapsed = time.time() - start
    
    print(f"⏱️  Latency: {elapsed:.2f}s")
    print(f"📝 Response length: {len(response)} chars")
    print(f"📝 Preview: {response[:200]}...")
    print(f"✅ Status: {'GOOD' if elapsed < 5 else 'SLOW'}")
    return elapsed

def test_complex_query():
    """Test with a complex query"""
    print("\n" + "="*80)
    print("TEST 3: Complex Analysis Query (should be <8s)")
    print("="*80)
    
    messages = [
        {"role": "system", "content": "You are a financial advisor analyzing investment portfolios."},
        {"role": "user", "content": """
Based on this portfolio data:
- Total value: ₹6.27 lakhs
- Equity: 87.86%
- Debt: 12.14%
- Top 3 holdings: 60% of portfolio

Should I rebalance? Give detailed reasoning.
"""}
    ]
    
    start = time.time()
    response = invoke_llm(messages, use_reasoning=False, stream=False)
    elapsed = time.time() - start
    
    print(f"⏱️  Latency: {elapsed:.2f}s")
    print(f"📝 Response length: {len(response)} chars")
    print(f"📝 Preview: {response[:300]}...")
    print(f"✅ Status: {'GOOD' if elapsed < 8 else 'SLOW'}")
    return elapsed

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 GPT-5-MINI ISOLATED BENCHMARK")
    print("="*80)
    print(f"\n📋 Configuration:")
    print(f"   Model: {config.PRIMARY_LLM_MODEL}")
    print(f"   Max Tokens: {config.MAX_COMPLETION_TOKENS_PRIMARY}")
    print(f"   Timeout: {config.PRIMARY_TIMEOUT}s")
    print()
    
    t1 = test_simple_query()
    t2 = test_medium_query()
    t3 = test_complex_query()
    
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"Simple query:  {t1:.2f}s {'✅' if t1 < 2 else '❌'}")
    print(f"Medium query:  {t2:.2f}s {'✅' if t2 < 5 else '❌'}")
    print(f"Complex query: {t3:.2f}s {'✅' if t3 < 8 else '❌'}")
    print(f"\nAverage: {(t1+t2+t3)/3:.2f}s")
    
    if (t1 + t2 + t3) / 3 > 6:
        print("\n⚠️  WARNING: gpt-5-mini is slower than expected!")
        print("Recommendations:")
        print("1. Reduce MAX_COMPLETION_TOKENS_PRIMARY further (try 1000-1500)")
        print("2. Enable streaming in production UI for better perceived performance")
        print("3. Consider using temperature=0.7 for faster responses")
        print("4. Check OpenAI API status - there might be rate limiting")
    else:
        print("\n✅ Performance is acceptable!")
    
    print("\n" + "="*80)

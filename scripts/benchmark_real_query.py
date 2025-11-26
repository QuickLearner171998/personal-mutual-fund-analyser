#!/usr/bin/env python3
"""
Real-world query benchmark - Measure actual performance
Tests the full orchestrator pipeline with a real user query
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
import json
from datetime import datetime
from agents.orchestrator import MultiAgentOrchestrator
from utils.logger import get_logger

logger = get_logger(__name__)

def benchmark_real_query():
    """
    Benchmark a real portfolio rebalancing query
    """
    print("="*80)
    print("🎯 REAL-WORLD QUERY BENCHMARK")
    print("="*80)
    print()
    
    # The actual user query
    query = "Should I rebalance my portfolio in the current market conditions?"
    
    print(f"📝 Query: {query}")
    print()
    print("⏳ Processing...")
    print()
    
    # Initialize orchestrator
    orchestrator = MultiAgentOrchestrator()
    
    # Measure end-to-end latency
    start_time = time.time()
    
    try:
        # Process the query (this goes through the full pipeline)
        response = orchestrator.process_query(query)
        
        elapsed = time.time() - start_time
        
        print("="*80)
        print("✅ SUCCESS")
        print("="*80)
        print(f"⏱️  Total Latency: {elapsed:.2f}s")
        print(f"📝 Response Length: {len(response)} characters")
        print()
        print("="*80)
        print("📄 RESPONSE PREVIEW (first 500 chars)")
        print("="*80)
        print(response[:500])
        if len(response) > 500:
            print("...")
            print()
            print(f"(... {len(response) - 500} more characters)")
        print()
        print("="*80)
        
        # Save detailed results
        result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "query": query,
            "success": True,
            "latency_seconds": elapsed,
            "response_length": len(response),
            "response_preview": response[:500],
            "full_response": response
        }
        
        with open("real_query_benchmark_results.json", "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"💾 Full results saved to: real_query_benchmark_results.json")
        print()
        
        # Performance analysis
        print("="*80)
        print("📊 PERFORMANCE ANALYSIS")
        print("="*80)
        
        if elapsed < 3:
            print("🚀 EXCELLENT: Sub-3 second response time!")
        elif elapsed < 5:
            print("✅ GOOD: Response under 5 seconds")
        elif elapsed < 8:
            print("⚠️  ACCEPTABLE: Response under 8 seconds, but could be faster")
        else:
            print("❌ SLOW: Response time exceeds 8 seconds")
            print("   Consider optimizing:")
            print("   - Reduce MAX_COMPLETION_TOKENS_PRIMARY")
            print("   - Enable streaming in UI")
            print("   - Use faster model for primary LLM")
        
        print()
        print("Breakdown estimate:")
        print("  - Intent Classification (gpt-4.1-mini): ~2-3s")
        print("  - Portfolio Data Retrieval: ~0.5s")
        print(f"  - Primary LLM Response (gpt-5-mini): ~{elapsed - 3:.1f}s")
        print()
        
        return result
        
    except Exception as e:
        elapsed = time.time() - start_time
        
        print("="*80)
        print("❌ FAILED")
        print("="*80)
        print(f"⏱️  Time to failure: {elapsed:.2f}s")
        print(f"❗ Error: {str(e)}")
        print()
        
        import traceback
        traceback.print_exc()
        
        result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "query": query,
            "success": False,
            "latency_seconds": elapsed,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        
        with open("real_query_benchmark_results.json", "w") as f:
            json.dump(result, f, indent=2)
        
        return result


if __name__ == "__main__":
    print()
    print("🚀 Starting real-world query benchmark...")
    print()
    
    result = benchmark_real_query()
    
    print()
    print("="*80)
    print("✅ BENCHMARK COMPLETED")
    print("="*80)
    print()

"""
GPT-5 Model Verification and Benchmark Script
Tests reasoning models with latest changes and measures performance
"""
import sys
from pathlib import Path
import time
from typing import Dict, List
import json

sys.path.insert(0, str(Path(__file__).parent))

from llm.llm_wrapper import invoke_llm, LLMWrapper
from utils.logger import get_logger
import config

logger = get_logger(__name__)

class GPT5Benchmark:
    def __init__(self):
        self.results = []
        self.wrapper = LLMWrapper()
        
    def run_test(self, test_name: str, messages: List[Dict], use_reasoning: bool = False, 
                 use_intent: bool = False, reasoning_effort: str = None) -> Dict:
        """
        Run a single test and measure performance
        
        Returns:
            Dict with test results
        """
        print(f"\n{'='*80}")
        print(f"TEST: {test_name}")
        print(f"{'='*80}")
        print(f"Reasoning: {use_reasoning}")
        print(f"Intent: {use_intent}")
        if reasoning_effort:
            print(f"Effort: {reasoning_effort}")
        
        start_time = time.time()
        
        try:
            response = invoke_llm(
                messages=messages,
                use_reasoning=use_reasoning,
                use_intent=use_intent,
                reasoning_effort=reasoning_effort,
                stream=False
            )
            
            elapsed = time.time() - start_time
            
            result = {
                'test_name': test_name,
                'success': True,
                'latency': elapsed,
                'response_length': len(response),
                'use_reasoning': use_reasoning,
                'use_intent': use_intent,
                'reasoning_effort': reasoning_effort,
                'response_preview': response[:200] + '...' if len(response) > 200 else response,
                'error': None
            }
            
            print(f"✅ SUCCESS")
            print(f"⏱️  Latency: {elapsed:.2f}s")
            print(f"📝 Response length: {len(response)} chars")
            print(f"📄 Preview: {response[:150]}...")
            
        except Exception as e:
            elapsed = time.time() - start_time
            
            result = {
                'test_name': test_name,
                'success': False,
                'latency': elapsed,
                'response_length': 0,
                'use_reasoning': use_reasoning,
                'use_intent': use_intent,
                'reasoning_effort': reasoning_effort,
                'response_preview': None,
                'error': str(e)
            }
            
            print(f"❌ FAILED")
            print(f"⏱️  Time to failure: {elapsed:.2f}s")
            print(f"❗ Error: {str(e)}")
        
        self.results.append(result)
        return result
    
    def test_model_detection(self):
        """Test if models are correctly identified as reasoning models"""
        print(f"\n{'='*80}")
        print("MODEL DETECTION TEST")
        print(f"{'='*80}")
        
        test_models = [
            "gpt-5",
            "gpt-5-mini",
            "o1-preview",
            "o1-mini",
            "gpt-4.1-mini",
            "gpt-4o",
        ]
        
        for model in test_models:
            is_reasoning = self.wrapper._is_reasoning_model(model)
            symbol = "🧠" if is_reasoning else "⚡"
            print(f"{symbol} {model}: {'Reasoning Model' if is_reasoning else 'Standard Model'}")
    
    def test_primary_model(self):
        """Test PRIMARY_LLM_MODEL"""
        messages = [{
            "role": "user",
            "content": "Explain XIRR in one sentence."
        }]
        
        return self.run_test(
            f"Primary Model ({config.PRIMARY_LLM_MODEL})",
            messages,
            use_reasoning=False
        )
    
    def test_intent_classification(self):
        """Test INTENT_CLASSIFICATION_MODEL"""
        messages = [{
            "role": "user",
            "content": "What is my portfolio value?"
        }]
        
        return self.run_test(
            f"Intent Classification ({config.INTENT_CLASSIFICATION_MODEL})",
            messages,
            use_reasoning=False,
            use_intent=True  # Use intent model, not primary
        )
    
    def test_reasoning_low(self):
        """Test reasoning model with low effort"""
        messages = [{
            "role": "user",
            "content": "Should I rebalance a portfolio with 90% equity and 10% debt?"
        }]
        
        return self.run_test(
            f"Reasoning Low ({config.REASONING_LLM_MODEL})",
            messages,
            use_reasoning=True,
            reasoning_effort="low"
        )
    
    def test_reasoning_medium(self):
        """Test reasoning model with medium effort"""
        messages = [{
            "role": "user",
            "content": "Analyze investment strategy: 70% large cap, 20% mid cap, 10% small cap. Market is volatile."
        }]
        
        return self.run_test(
            f"Reasoning Medium ({config.REASONING_LLM_MODEL})",
            messages,
            use_reasoning=True,
            reasoning_effort="medium"
        )
    
    def test_reasoning_high(self):
        """Test reasoning model with high effort"""
        messages = [{
            "role": "user",
            "content": "Comprehensive analysis: Portfolio has 15 funds, total value 10L, XIRR 12%. Market cap split: 60% large, 25% mid, 15% small. Sector: 30% tech, 25% finance, 20% pharma, 15% auto, 10% FMCG. Should I rebalance? Consider tax implications, market conditions, and risk tolerance."
        }]
        
        return self.run_test(
            f"Reasoning High ({config.REASONING_LLM_MODEL})",
            messages,
            use_reasoning=True,
            reasoning_effort="high"
        )
    
    def print_configuration(self):
        """Print current model configuration"""
        print(f"\n{'='*80}")
        print("CURRENT CONFIGURATION")
        print(f"{'='*80}")
        
        print(f"\n🔧 Model Configuration:")
        print(f"  PRIMARY_LLM_MODEL:            {config.PRIMARY_LLM_MODEL}")
        print(f"  REASONING_LLM_MODEL:          {config.REASONING_LLM_MODEL}")
        print(f"  INTENT_CLASSIFICATION_MODEL:  {config.INTENT_CLASSIFICATION_MODEL}")
        print(f"  RAG_LLM_MODEL:                {config.RAG_LLM_MODEL}")
        print(f"  FALLBACK_LLM_MODEL:           {config.FALLBACK_LLM_MODEL}")
        
        print(f"\n⚡ Performance Settings:")
        print(f"  REASONING_EFFORT_DEFAULT:     {config.REASONING_EFFORT_DEFAULT}")
        print(f"  MAX_COMPLETION_TOKENS_REASONING: {config.MAX_COMPLETION_TOKENS_REASONING}")
        print(f"  MAX_COMPLETION_TOKENS_PRIMARY:   {config.MAX_COMPLETION_TOKENS_PRIMARY}")
        print(f"  REASONING_TIMEOUT:            {config.REASONING_TIMEOUT}s")
        print(f"  PRIMARY_TIMEOUT:              {config.PRIMARY_TIMEOUT}s")
        print(f"  ENABLE_PROMPT_CACHING:        {config.ENABLE_PROMPT_CACHING}")
        print(f"  INCLUDE_REASONING:            {config.INCLUDE_REASONING}")
    
    def print_summary(self):
        """Print benchmark summary"""
        print(f"\n{'='*80}")
        print("BENCHMARK SUMMARY")
        print(f"{'='*80}")
        
        successful_tests = [r for r in self.results if r['success']]
        failed_tests = [r for r in self.results if not r['success']]
        
        print(f"\n📊 Overall Results:")
        print(f"  Total Tests:     {len(self.results)}")
        print(f"  ✅ Successful:   {len(successful_tests)}")
        print(f"  ❌ Failed:       {len(failed_tests)}")
        
        if successful_tests:
            print(f"\n⏱️  Latency Analysis:")
            print(f"  {'Test Name':<40} {'Latency':<12} {'Status'}")
            print(f"  {'-'*40} {'-'*12} {'-'*10}")
            
            for result in self.results:
                status = "✅ OK" if result['success'] else "❌ FAIL"
                latency = f"{result['latency']:.2f}s" if result['success'] else f"FAIL {result['latency']:.2f}s"
                print(f"  {result['test_name']:<40} {latency:<12} {status}")
            
            # Calculate averages
            avg_latency = sum(r['latency'] for r in successful_tests) / len(successful_tests)
            min_latency = min(r['latency'] for r in successful_tests)
            max_latency = max(r['latency'] for r in successful_tests)
            
            print(f"\n  Average Latency: {avg_latency:.2f}s")
            print(f"  Min Latency:     {min_latency:.2f}s")
            print(f"  Max Latency:     {max_latency:.2f}s")
        
        if failed_tests:
            print(f"\n❌ Failed Tests Details:")
            for result in failed_tests:
                print(f"\n  Test: {result['test_name']}")
                print(f"  Error: {result['error']}")
        
        # Reasoning effort comparison
        reasoning_tests = [r for r in successful_tests if r['use_reasoning']]
        if reasoning_tests:
            print(f"\n🧠 Reasoning Effort Comparison:")
            efforts = {}
            for r in reasoning_tests:
                effort = r['reasoning_effort']
                if effort not in efforts:
                    efforts[effort] = []
                efforts[effort].append(r['latency'])
            
            for effort, latencies in sorted(efforts.items()):
                avg = sum(latencies) / len(latencies)
                print(f"  {effort.upper():<8}: {avg:.2f}s average")
    
    def save_results(self, filename: str = "benchmark_results.json"):
        """Save results to JSON file"""
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'configuration': {
                    'PRIMARY_LLM_MODEL': config.PRIMARY_LLM_MODEL,
                    'REASONING_LLM_MODEL': config.REASONING_LLM_MODEL,
                    'REASONING_EFFORT_DEFAULT': config.REASONING_EFFORT_DEFAULT,
                },
                'results': self.results
            }, f, indent=2)
        print(f"\n💾 Results saved to {filename}")


def main():
    """Run full benchmark suite"""
    print("\n" + "🚀 "*40)
    print("GPT-5 MODEL VERIFICATION & BENCHMARK")
    print("🚀 "*40)
    
    benchmark = GPT5Benchmark()
    
    # Print configuration
    benchmark.print_configuration()
    
    # Test model detection
    benchmark.test_model_detection()
    
    print(f"\n{'='*80}")
    print("RUNNING BENCHMARKS")
    print(f"{'='*80}")
    print("\nNote: Some tests may take 30+ seconds. Please be patient...")
    
    # Run tests in order of increasing complexity
    print("\n📍 Phase 1: Fast Models")
    benchmark.test_intent_classification()
    benchmark.test_primary_model()
    
    print("\n📍 Phase 2: Reasoning Models (Low to High Effort)")
    print("⚠️  Warning: The following tests may be slow and consume API credits")
    print("Comment out in code if you want to skip these tests\n")
    
    # Uncomment to test reasoning models
    # benchmark.test_reasoning_low()
    # benchmark.test_reasoning_medium()
    # benchmark.test_reasoning_high()
    
    # Print summary
    benchmark.print_summary()
    
    # Save results
    benchmark.save_results()
    
    print(f"\n{'='*80}")
    print("✅ BENCHMARK COMPLETED")
    print(f"{'='*80}")
    print("\nRecommendations:")
    print("1. If PRIMARY_LLM uses gpt-5-mini, ensure it supports reasoning_effort")
    print("2. For fast queries, use gpt-4.1-mini (intent/rag models)")
    print("3. For complex analysis, use full gpt-5 with appropriate effort")
    print("4. Monitor latency and adjust reasoning_effort accordingly")
    print("\nTo test reasoning models, uncomment the test calls in main()")


if __name__ == "__main__":
    main()

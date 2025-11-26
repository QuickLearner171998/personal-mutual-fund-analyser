#!/usr/bin/env python3
"""
Test the new planning-based orchestrator
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.orchestrator import MultiAgentOrchestrator
from utils.logger import get_logger

logger = get_logger(__name__)

def test_query(query: str):
    """Test a single query"""
    print("\n" + "="*80)
    print(f"QUERY: {query}")
    print("="*80)
    
    orchestrator = MultiAgentOrchestrator()
    
    try:
        response = orchestrator.process_query(query)
        print("\nRESPONSE:")
        print(response[:500] if len(response) > 500 else response)
        if len(response) > 500:
            print(f"\n... ({len(response) - 500} more characters)")
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*80)
    print("TESTING PLANNING-BASED ORCHESTRATOR")
    print("="*80)
    
    # Test different types of queries
    queries = [
        "What is my total investment?",  # Should use: portfolio
        "Should I shift from large cap to mid/small cap?",  # Should use: portfolio + market + strategy
        "Latest NAV of HDFC Flexi Cap",  # Should use: market
    ]
    
    for query in queries:
        test_query(query)
    
    print("\n" + "="*80)
    print("TESTS COMPLETED")
    print("="*80)

#!/usr/bin/env python3
"""
Main test runner for MF Portfolio Bot
Run locally without Streamlit
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_config():
    """Test configuration"""
    print("Testing configuration...")
    import config
    print(f"✓ Primary LLM: {config.PRIMARY_LLM_MODEL}")
    print(f"✓ RAG LLM: {config.RAG_LLM_MODEL}")
    print(f"✓ Reasoning LLM: {config.REASONING_LLM_MODEL}")
    print(f"✓ Data directory: {config.DATA_DIR}")
    print()

def test_portfolio_store():
    """Test portfolio JSON storage"""
    print("Testing portfolio storage...")
    from database.json_store import PortfolioStore
    
    store = PortfolioStore()
    portfolio = store.get_portfolio()
    
    if portfolio:
        print(f"✓ Portfolio loaded")
        print(f"  Total value: ₹{portfolio.get('total_value', 0):,.0f}")
        print(f"  Holdings: {len(portfolio.get('holdings', []))}")
    else:
        print("⚠ No portfolio data found (upload CAS first)")
    print()

def test_llm():
    """Test LLM wrapper"""
    print("Testing LLM...")
    try:
        from llm.llm_wrapper import invoke_llm
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello' in one word."}
        ]
        
        response = invoke_llm(messages, use_rag=True, stream=False)
        print(f"✓ LLM Response: {response}")
    except Exception as e:
        print(f"✗ LLM Error: {str(e)}")
    print()

def test_agents():
    """Test multi-agent system"""
    print("Testing agents...")
    try:
        from agents.orchestrator import answer_query
        
        # Test query
        query = "What is XIRR?"
        print(f"Query: {query}")
        response = answer_query(query, stream=False)
        print(f"Response: {response[:200]}...")
        
        # Test Portfolio Query (to verify invoke_llm fix)
        query_portfolio = "What is my total investment?"
        print(f"\nQuery: {query_portfolio}")
        response_portfolio = answer_query(query_portfolio, stream=False)
        print(f"Response: {response_portfolio[:200]}...")
        
        # Test Market Query (Perplexity)
        print("\nTesting Market Agent (Perplexity)...")
        from agents.market_agent import MarketAgent
        market_agent = MarketAgent()
        market_response = market_agent.research("Current NAV of SBI Small Cap Fund")
        print(f"Market Response: {market_response[:200]}...")
        
        print("✓ Agents working")
    except Exception as e:
        print(f"✗ Agent Error: {str(e)}")
    print()

def test_calculations():
    """Test financial calculations"""
    print("Testing calculations...")
    try:
        from calculations.returns import calculate_xirr, calculate_cagr
        from datetime import date
        
        # Test CAGR
        cagr = calculate_cagr(100000, 150000, 3)
        print(f"✓ CAGR (₹1L → ₹1.5L in 3Y): {cagr:.2f}%")
        
        # Test XIRR
        transactions = [
            {'date': date(2020, 1, 1), 'amount': 100000, 'type': 'purchase'},
            {'date': date(2023, 1, 1), 'amount': 150000, 'type': 'redemption'}
        ]
        xirr = calculate_xirr(transactions)
        print(f"✓ XIRR: {xirr:.2f}%")
    except Exception as e:
        print(f"✗ Calculation Error: {str(e)}")
    print()

def main():
    """Run all tests"""
    print("="*60)
    print("MF Portfolio Bot - Local Test Runner")
    print("="*60)
    print()
    
    test_config()
    test_portfolio_store()
    test_calculations()
    test_llm()
    test_agents()
    test_comprehensive()
    
    print("="*60)
    print("All tests completed!")

def test_comprehensive():
    """Run comprehensive unit tests"""
    print("Running comprehensive tests...")
    import unittest
    from tests.test_comprehensive import TestPortfolioAnalysis
    
    # Load tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPortfolioAnalysis)
    
    # Run tests
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    if not result.wasSuccessful():
        print("❌ Comprehensive tests failed!")
        sys.exit(1)
    else:
        print("✓ Comprehensive tests passed!")
    print()
    print("="*60)
    print()
    print("To run the full app:")
    print("  streamlit run app.py")
    print()

if __name__ == "__main__":
    main()

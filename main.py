#!/usr/bin/env python3
"""
Main test runner for MF Portfolio Analyzer
Tests all components and runs business logic without UI
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.portfolio_processor import (
    load_mf_central_files,
    validate_mf_central_data,
    process_mf_central_data,
    get_portfolio_summary,
    get_transaction_summary,
    load_portfolio_from_db,
    check_sample_files_exist
)


def test_imports():
    """Test all critical imports"""
    print("=" * 80)
    print("IMPORT TEST")
    print("=" * 80)
    
    try:
        # Core imports
        print("\n1. Testing core imports...")
        import config
        from database.json_store import PortfolioStore
        from cas_import.mf_central_parser import MFCentralParser
        from calculations.returns import calculate_cagr, calculate_allocation
        print("   ✓ Core imports successful")
        
        # UI imports
        print("\n2. Testing UI imports...")
        try:
            from ui.dashboard import render_dashboard
            from ui.sip_analytics import render_sip_dashboard
            from ui.cas_upload import render_upload_page
            from ui.chat import render_chat
            print("   ✓ UI imports successful")
        except ImportError as e:
            print(f"   ⚠️  UI import warning: {str(e)}")
            print("   (This is OK if Streamlit is not installed)")
        
        # Agent imports
        print("\n3. Testing agent imports...")
        from agents.coordinator import IntentClassifier
        from agents.portfolio_agent import PortfolioAgent
        from llm.llm_wrapper import invoke_llm
        print("   ✓ Agent imports successful")
        
        # Vector DB imports
        print("\n4. Testing vector DB imports...")
        from vector_db.portfolio_indexer import index_portfolio_data
        from vector_db.faiss_store import LocalVectorStore
        print("   ✓ Vector DB imports successful")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Import Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_mf_central_parser():
    """Test MF Central parser with sample data"""
    print("\n" + "=" * 80)
    print("MF CENTRAL PARSER TEST")
    print("=" * 80)
    
    # Check if sample files exist
    files_exist, missing = check_sample_files_exist()
    
    if not files_exist:
        print(f"\n⚠️  Sample data files not found: {', '.join(missing)}")
        print("Please upload MF Central files first.")
        return False
    
    # File paths
    base_dir = Path(__file__).parent
    consolidated_path = base_dir / "CCJN4KTLB310840997771IMBAS199068013/CurrentValuationAS199068013.json"
    transaction_path = base_dir / "CCJN4KTLB310840997771IMBAS199068013/AS199068013.json"
    detailed_path = base_dir / "70910727520211641ZF683740997FF11IMBPF199067986.json"
    
    try:
        # Load files
        print("\n1. Loading JSON files...")
        consolidated_data, transaction_data, detailed_data = load_mf_central_files(
            consolidated_path,
            transaction_path,
            detailed_path
        )
        print(f"   ✓ Loaded consolidated portfolio: {len(consolidated_data['dtTrxnResult'])} entries")
        print(f"   ✓ Loaded transactions: {len(transaction_data['dtTrxnResult'])} entries")
        print(f"   ✓ Loaded detailed report: {len(detailed_data)} entries")
        
        # Validate
        print("\n2. Validating data...")
        is_valid, error = validate_mf_central_data(consolidated_data, transaction_data, detailed_data)
        if not is_valid:
            print(f"   ✗ Validation error: {error}")
            return False
        print("   ✓ Data validation successful")
        
        # Process
        print("\n3. Processing data...")
        portfolio_data, transactions = process_mf_central_data(
            consolidated_data,
            transaction_data,
            detailed_data,
            save_to_db=True,
            index_for_qa=True
        )
        print("   ✓ Data processing successful")
        
        # Display summary
        print("\n" + "=" * 80)
        print("PORTFOLIO SUMMARY")
        print("=" * 80)
        
        summary = get_portfolio_summary(portfolio_data)
        print(f"\nInvestor: {summary['investor_name']}")
        print(f"PAN: {summary['pan']}")
        print(f"\nTotal Value: ₹{summary['total_value']:,.2f}")
        print(f"Total Invested: ₹{summary['total_invested']:,.2f}")
        print(f"Total Gain: ₹{summary['total_gain']:,.2f} ({summary['total_gain_percent']:.2f}%)")
        print(f"Portfolio XIRR: {summary['xirr']:.2f}%")
        print(f"\nFunds: {summary['num_funds']}")
        print(f"Aggregated Funds: {summary['num_aggregated_funds']}")
        print(f"Active SIPs: {summary['num_active_sips']}")
        print(f"Brokers: {summary['num_brokers']}")
        
        # Transaction summary
        txn_summary = get_transaction_summary(transactions)
        print(f"\nTotal Transactions: {txn_summary['total']}")
        for txn_type, count in txn_summary['by_type'].items():
            print(f"  {txn_type}: {count}")
        
        print("\n" + "=" * 80)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """Test configuration"""
    print("\n" + "=" * 80)
    print("CONFIGURATION TEST")
    print("=" * 80)
    
    try:
        import config
        print(f"\n✓ Primary LLM: {config.PRIMARY_LLM_MODEL}")
        print(f"✓ RAG LLM: {config.RAG_LLM_MODEL}")
        print(f"✓ Reasoning LLM: {config.REASONING_LLM_MODEL}")
        print(f"✓ Data directory: {config.DATA_DIR}")
        return True
    except Exception as e:
        print(f"\n✗ Config Error: {str(e)}")
        return False


def test_portfolio_store():
    """Test portfolio storage"""
    print("\n" + "=" * 80)
    print("PORTFOLIO STORAGE TEST")
    print("=" * 80)
    
    try:
        portfolio = load_portfolio_from_db()
        
        if portfolio:
            summary = get_portfolio_summary(portfolio)
            print(f"\n✓ Portfolio loaded from storage")
            print(f"  Total value: ₹{summary['total_value']:,.0f}")
            print(f"  Holdings: {len(portfolio.get('holdings', []))}")
            print(f"  Active SIPs: {summary['num_active_sips']}")
            print(f"  Data source: {summary['data_source']}")
            return True
        else:
            print("\n⚠️  No portfolio data in storage")
            return False
    except Exception as e:
        print(f"\n✗ Storage Error: {str(e)}")
        return False


def test_calculations():
    """Test financial calculations"""
    print("\n" + "=" * 80)
    print("CALCULATIONS TEST")
    print("=" * 80)
    
    try:
        from calculations.returns import calculate_cagr, calculate_allocation
        
        # Test CAGR
        cagr = calculate_cagr(100000, 150000, 3)
        print(f"\n✓ CAGR (₹1L → ₹1.5L in 3Y): {cagr:.2f}%")
        
        # Test allocation
        sample_holdings = [
            {'current_value': 100000, 'type': 'Equity', 'scheme_name': 'Large Cap Fund'},
            {'current_value': 50000, 'type': 'Debt', 'scheme_name': 'Debt Fund'},
        ]
        allocation = calculate_allocation(sample_holdings)
        print(f"✓ Allocation: Equity {allocation['equity']:.1f}%, Debt {allocation['debt']:.1f}%")
        
        return True
    except Exception as e:
        print(f"\n✗ Calculation Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("MF PORTFOLIO ANALYZER - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    results = []
    
    # Test 1: Imports (CRITICAL - must pass)
    results.append(("Imports", test_imports()))
    
    if not results[0][1]:
        print("\n❌ CRITICAL: Import test failed. Cannot continue.")
        sys.exit(1)
    
    # Test 2: Configuration
    results.append(("Configuration", test_config()))
    
    # Test 3: MF Central Parser
    results.append(("MF Central Parser", test_mf_central_parser()))
    
    # Test 4: Portfolio Storage
    results.append(("Portfolio Storage", test_portfolio_store()))
    
    # Test 5: Calculations
    results.append(("Calculations", test_calculations()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        print("\n" + "=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print("\nTo run the Streamlit app:")
        print("  streamlit run app.py")
        print("\nThe app will be available at: http://localhost:8501")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

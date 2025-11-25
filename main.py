#!/usr/bin/env python3
"""
Main test runner for MF Portfolio Analyzer
Tests MF Central data parsing and processing
"""
import sys
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_mf_central_parser():
    """Test MF Central parser with sample data"""
    print("=" * 80)
    print("MF CENTRAL PARSER TEST")
    print("=" * 80)
    
    from cas_import.mf_central_parser import MFCentralParser
    
    # File paths
    base_dir = Path(__file__).parent
    consolidated_path = base_dir / "CCJN4KTLB310840997771IMBAS199068013/CurrentValuationAS199068013.json"
    transaction_path = base_dir / "CCJN4KTLB310840997771IMBAS199068013/AS199068013.json"
    detailed_path = base_dir / "70910727520211641ZF683740997FF11IMBPF199067986.json"
    
    # Check if files exist
    if not all([consolidated_path.exists(), transaction_path.exists(), detailed_path.exists()]):
        print("\n⚠️  Sample data files not found. Please upload MF Central files first.")
        print("\nExpected files:")
        print(f"  1. {consolidated_path}")
        print(f"  2. {transaction_path}")
        print(f"  3. {detailed_path}")
        return False
    
    # Load files
    print("\n1. Loading JSON files...")
    
    with open(consolidated_path, 'r') as f:
        consolidated_data = json.load(f)
    print(f"   ✓ Loaded consolidated portfolio: {len(consolidated_data['dtTrxnResult'])} entries")
    
    with open(transaction_path, 'r') as f:
        transaction_data = json.load(f)
    print(f"   ✓ Loaded transactions: {len(transaction_data['dtTrxnResult'])} entries")
    
    with open(detailed_path, 'r') as f:
        detailed_data = json.load(f)
    print(f"   ✓ Loaded detailed report: {len(detailed_data)} entries")
    
    # Initialize parser
    print("\n2. Parsing data...")
    parser = MFCentralParser()
    
    try:
        portfolio_data = parser.build_portfolio_data(
            consolidated_data,
            transaction_data,
            detailed_data
        )
        print("   ✓ Portfolio data built successfully")
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Display summary
    print("\n" + "=" * 80)
    print("PORTFOLIO SUMMARY")
    print("=" * 80)
    
    print(f"\nInvestor: {portfolio_data['investor_name']}")
    print(f"PAN: {portfolio_data['pan']}")
    print(f"\nTotal Value: ₹{portfolio_data['total_value']:,.2f}")
    print(f"Total Invested: ₹{portfolio_data['total_invested']:,.2f}")
    print(f"Total Gain: ₹{portfolio_data['total_gain']:,.2f} ({portfolio_data['total_gain_percent']:.2f}%)")
    print(f"Portfolio XIRR: {portfolio_data['xirr']:.2f}%")
    
    print(f"\nFunds: {portfolio_data['num_funds']}")
    print(f"Aggregated Funds: {portfolio_data['num_aggregated_funds']}")
    print(f"Active SIPs: {portfolio_data['num_active_sips']}")
    print(f"Brokers: {portfolio_data['num_brokers']}")
    
    # Show active SIPs
    if portfolio_data['active_sips']:
        print("\n" + "-" * 80)
        print(f"ACTIVE SIPs ({len(portfolio_data['active_sips'])})")
        print("-" * 80)
        for sip in portfolio_data['active_sips'][:5]:  # Show first 5
            print(f"\n{sip['scheme_name'][:60]}")
            print(f"  Amount: ₹{sip['sip_amount']:,.2f} ({sip['frequency']})")
            print(f"  Total Invested: ₹{sip['total_invested']:,.2f}")
            print(f"  Broker: {sip['broker']}")
    
    # Show brokers
    if portfolio_data['broker_info']:
        print("\n" + "-" * 80)
        print(f"BROKERS ({len(portfolio_data['broker_info'])})")
        print("-" * 80)
        for broker, info in list(portfolio_data['broker_info'].items())[:5]:
            print(f"\n{broker}")
            print(f"  Total Invested: ₹{info['total_invested']:,.2f}")
            print(f"  Schemes: {info['scheme_count']}")
    
    # Show top 5 holdings
    print("\n" + "-" * 80)
    print("TOP 5 HOLDINGS BY VALUE")
    print("-" * 80)
    sorted_holdings = sorted(
        portfolio_data['holdings'], 
        key=lambda x: x['current_value'], 
        reverse=True
    )[:5]
    
    for i, holding in enumerate(sorted_holdings, 1):
        print(f"\n{i}. {holding['scheme_name'][:60]}")
        print(f"   Value: ₹{holding['current_value']:,.2f} | XIRR: {holding['xirr']:.2f}%")
    
    # Save to database
    print("\n" + "=" * 80)
    print("SAVING TO DATABASE")
    print("=" * 80)
    
    from database.json_store import PortfolioStore
    
    store = PortfolioStore()
    store.save_complete_data(
        portfolio=portfolio_data,
        transactions=parser.transaction_data,
        sips=portfolio_data.get('active_sips', []),
        broker_info=portfolio_data.get('broker_info', {}),
        aggregation_map=portfolio_data.get('aggregation_map', {})
    )
    print("\n✓ Portfolio data saved to ./data/")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)
    
    return True


def test_config():
    """Test configuration"""
    print("\n" + "=" * 80)
    print("CONFIGURATION TEST")
    print("=" * 80)
    
    try:
        import config
        print(f"\n✓ Primary LLM: {config.PRIMARY_LLM_MODEL}")
        print(f"✓ RAG LLM: {config.RAG_LLM_MODEL}")
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
        from database.json_store import PortfolioStore
        
        store = PortfolioStore()
        portfolio = store.get_portfolio()
        
        if portfolio:
            print(f"\n✓ Portfolio loaded from storage")
            print(f"  Total value: ₹{portfolio.get('total_value', 0):,.0f}")
            print(f"  Holdings: {len(portfolio.get('holdings', []))}")
            print(f"  Active SIPs: {portfolio.get('num_active_sips', 0)}")
            print(f"  Data source: {portfolio.get('data_source', 'Unknown')}")
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
    print("MF PORTFOLIO ANALYZER - TEST SUITE")
    print("=" * 80)
    
    results = []
    
    # Test 1: Configuration
    results.append(("Configuration", test_config()))
    
    # Test 2: MF Central Parser
    results.append(("MF Central Parser", test_mf_central_parser()))
    
    # Test 3: Portfolio Storage
    results.append(("Portfolio Storage", test_portfolio_store()))
    
    # Test 4: Calculations
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
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

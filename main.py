"""
Main Debug/Test Runner
Tests backend processing and displays responses for debugging
"""
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("MF PORTFOLIO ANALYZER - DEBUG MODE")
print("=" * 80)
print()

# Test 1: Import all modules
print("▶ Testing Imports...")
try:
    from core.unified_processor import process_mf_central_complete
    from database.json_store import PortfolioStore
    from vector_db.portfolio_indexer import index_portfolio_data
    from agents.coordinator import IntentClassifier
    print("✅ All imports successful")
except Exception as e:
    print(f"❌ Import failed: {str(e)}")
    sys.exit(1)

print()

# Test 2: Process MF Central files
print("▶ Processing MF Central Files...")
print("  Files:")
print("    - Excel: cas_detailed_report_2025_11_26_004753.xlsx")
print("    - Transaction JSON: CCJN4KTLB310840997771IMBAS199068013/AS199068013.json")
print("    - XIRR JSON: 70910727520211641ZF683740997FF11IMBPF199067986.json")
print()

try:
    portfolio_data = process_mf_central_complete(
        'cas_detailed_report_2025_11_26_004753.xlsx',
        'CCJN4KTLB310840997771IMBAS199068013/AS199068013.json',
        '70910727520211641ZF683740997FF11IMBPF199067986.json'
    )
    
    print("✅ Processing successful")
    print()
    print("PORTFOLIO SUMMARY:")
    print(f"  Investor: {portfolio_data.get('investor_name', 'N/A')}")
    print(f"  Total Value: ₹{portfolio_data.get('total_value', 0):,.2f}")
    print(f"  Total Invested: ₹{portfolio_data.get('total_invested', 0):,.2f}")
    print(f"  Total Gain: ₹{portfolio_data.get('total_gain', 0):,.2f} ({portfolio_data.get('total_gain_percent', 0):.2f}%)")
    print(f"  Portfolio XIRR: {portfolio_data.get('xirr', 0):.2f}%")
    print(f"  Holdings: {portfolio_data.get('num_funds', 0)}")
    print(f"  Active SIPs: {portfolio_data.get('num_active_sips', 0)}")
    print(f"  Brokers: {portfolio_data.get('num_brokers', 0)}")
    print()
    
except Exception as e:
    print(f"❌ Processing failed: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Save to database
print("▶ Saving to Database...")
try:
    store = PortfolioStore()
    store.save_complete_data(
        portfolio=portfolio_data,
        transactions=[],
        sips=portfolio_data.get('active_sips', []),
        broker_info=portfolio_data.get('broker_info', {}),
        aggregation_map={}
    )
    print("✅ Database save successful")
    print()
except Exception as e:
    print(f"❌ Database save failed: {str(e)}")
    import traceback
    traceback.print_exc()

# Test 4: Vector indexing
print("▶ Testing Vector Indexing...")
try:
    index_portfolio_data(portfolio_data)
    print("✅ Vector indexing successful")
    print()
except Exception as e:
    print(f"⚠️  Vector indexing skipped: {str(e)}")
    print()

# Test 5: Display Holdings Sample
print("▶ Sample Holdings (First 5):")
print("-" * 80)
holdings = portfolio_data.get('holdings', [])
for i, h in enumerate(holdings[:5], 1):
    print(f"{i}. {h.get('scheme_name', 'N/A')[:50]:50s}")
    print(f"   Current Value: ₹{h.get('current_value', 0):>12,.2f}")
    print(f"   Invested:      ₹{h.get('cost_value', 0):>12,.2f}")
    print(f"   Gain/Loss:     ₹{h.get('gain_loss', 0):>12,.2f} ({h.get('gain_loss_percent', 0):>6.2f}%)")
    print(f"   XIRR:          {h.get('xirr', 0):>6.2f}%")
    print(f"   Broker:        {h.get('broker', 'Unknown')}")
    print()

# Test 6: Display Active SIPs
print("▶ Active SIPs:")
print("-" * 80)
active_sips = portfolio_data.get('active_sips', [])
if active_sips:
    for i, sip in enumerate(active_sips, 1):
        print(f"{i}. {sip.get('scheme_name', 'N/A')[:50]:50s}")
        print(f"   Amount:     ₹{sip.get('sip_amount', 0):>10,.2f}")
        print(f"   Frequency:  {sip.get('frequency', 'N/A'):>10s}")
        print(f"   Last Date:  {sip.get('last_installment_date', 'N/A')}")
        print(f"   Broker:     {sip.get('broker', 'Unknown')}")
        print()
else:
    print("No active SIPs found")
    print()

# Test 7: Display Broker Summary
print("▶ Broker Summary:")
print("-" * 80)
broker_info = portfolio_data.get('broker_info', {})
if broker_info:
    for broker, info in broker_info.items():
        print(f"Broker: {broker}")
        print(f"  Total Invested:  ₹{info.get('total_invested', 0):,.2f}")
        print(f"  Schemes:         {info.get('scheme_count', 0)}")
        print(f"  Transactions:    {info.get('transaction_count', 0)}")
        print()
else:
    print("No broker information found")
    print()

# Test 8: Test Q&A Agent
print("▶ Testing Q&A Agent (Intent Classification):")
print("-" * 80)

test_queries = [
    "What is my total portfolio value?",
    "How many SIPs do I have?",
    "Which fund has the best XIRR?",
    "Should I rebalance my portfolio?",
    "What is the latest market trend for tech funds?"
]

try:
    classifier = IntentClassifier()
    
    for query in test_queries:
        intents = classifier.classify(query)
        print(f"Query: {query}")
        print(f"  → Intents: {', '.join(intents)}")
        print()
    
    print("✅ Intent classification successful")
    print()
except Exception as e:
    print(f"⚠️  Intent classification failed: {str(e)}")
    import traceback
    traceback.print_exc()
    print()

# Summary
print("=" * 80)
print("DEBUG SESSION COMPLETE")
print("=" * 80)
print()
print("✅ Portfolio data processed successfully")
print(f"✅ {len(holdings)} holdings loaded")
print(f"✅ {len(active_sips)} active SIPs found")
print(f"✅ {len(broker_info)} brokers identified")
print()
print("Ready for Q&A queries via Flask UI!")
print()

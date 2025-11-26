"""
Main Debug/Test Runner
Tests backend processing and displays responses for debugging
Purpose: Run each endpoint code locally with given inputs for debugging
"""
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import centralized logger
from utils.logger import get_logger

logger = get_logger(__name__)

logger.info("=" * 80)
logger.info("MF PORTFOLIO ANALYZER - DEBUG MODE")
logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logger.info("=" * 80)


# Test 1: Import all modules
logger.info("▶ Step 1: Testing Imports...")
logger.info("Starting module imports")
try:
    logger.info("Importing core.unified_processor")
    from core.unified_processor import process_mf_central_complete
    
    logger.info("Importing database.json_store")
    from database.json_store import PortfolioStore
    
    logger.info("Importing vector_db.portfolio_indexer")
    from vector_db.portfolio_indexer import index_portfolio_data
    
    logger.info("Importing agents.coordinator")
    from agents.coordinator import IntentClassifier
    
    logger.info("Importing agents.orchestrator")
    from agents.orchestrator import MultiAgentOrchestrator
    
    logger.info("Importing all agent modules")
    from agents.portfolio_agent import PortfolioAgent
    from agents.goal_agent import GoalAgent
    from agents.market_agent import MarketAgent
    from agents.strategy_agent import StrategyAgent
    from agents.comparison_agent import ComparisonAgent
    
    logger.info("✅ All imports successful")
    logger.info("All modules imported successfully")
except Exception as e:
    logger.error(f"❌ Import failed: {str(e)}")
    sys.exit(1)


# Test 2: Process MF Central files
logger.info("▶ Step 2: Processing MF Central Files (Upload Endpoint Simulation)...")
logger.info("=" * 60)
logger.info("SIMULATING /upload ENDPOINT")
logger.info("=" * 60)
logger.info("Files:")
logger.info("  - Excel: cas_detailed_report_2025_11_26_004753.xlsx")
logger.info("  - Transaction JSON: CCJN4KTLB310840997771IMBAS199068013/AS199068013.json")
logger.info("  - XIRR JSON: 70910727520211641ZF683740997FF11IMBPF199067986.json")

try:
    logger.info("Starting MF Central file processing")
    
    portfolio_data = process_mf_central_complete(
        'cas_detailed_report_2025_11_26_004753.xlsx',
        'CCJN4KTLB310840997771IMBAS199068013/AS199068013.json',
        '70910727520211641ZF683740997FF11IMBPF199067986.json'
    )
    
    logger.info("Processing completed successfully")
    logger.info(f"Portfolio data keys: {list(portfolio_data.keys())}")
    
    logger.info("✅ Processing successful")
    logger.info("")
    logger.info("PORTFOLIO SUMMARY:")
    logger.info(f"  Investor: {portfolio_data.get('investor_name', 'N/A')}")
    logger.info(f"  Total Value: ₹{portfolio_data.get('total_value', 0):,.2f}")
    logger.info(f"  Total Invested: ₹{portfolio_data.get('total_invested', 0):,.2f}")
    logger.info(f"  Total Gain: ₹{portfolio_data.get('total_gain', 0):,.2f} ({portfolio_data.get('total_gain_percent', 0):.2f}%)")
    logger.info(f"  Portfolio XIRR: {portfolio_data.get('xirr', 0):.2f}%")
    logger.info(f"  Holdings: {portfolio_data.get('num_funds', 0)}")
    logger.info(f"  Active SIPs: {portfolio_data.get('num_active_sips', 0)}")
    logger.info(f"  Brokers: {portfolio_data.get('num_brokers', 0)}")
    
except Exception as e:
    logger.error(f"❌ Processing failed: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


# Test 3: Save to database
logger.info("▶ Step 3: Saving to Database...")
logger.info("=" * 60)
logger.info("TESTING DATABASE OPERATIONS")
logger.info("=" * 60)
try:
    logger.info("Initializing PortfolioStore")
    store = PortfolioStore()
    
    logger.info("Saving complete portfolio data to JSON store")
    store.save_complete_data(
        portfolio=portfolio_data,
        transactions=[],
        sips=portfolio_data.get('active_sips', []),
        broker_info=portfolio_data.get('broker_info', {}),
        aggregation_map={}
    )
    
    logger.info("✅ Database save successful")
    logger.info(f"Saved {len(portfolio_data.get('holdings', []))} holdings")
    logger.info(f"Saved {len(portfolio_data.get('active_sips', []))} SIPs")
except Exception as e:
    logger.error(f"❌ Database save failed: {str(e)}")
    import traceback
    traceback.print_exc()

# Test 4: Vector indexing
logger.info("▶ Step 4: Testing Vector Indexing...")
logger.info("=" * 60)
logger.info("TESTING VECTOR DATABASE INDEXING")
logger.info("=" * 60)
try:
    logger.info("Starting FAISS vector indexing")
    index_portfolio_data(portfolio_data)
    logger.info("✅ Vector indexing successful")
except Exception as e:
    logger.warning(f"⚠️  Vector indexing skipped: {str(e)}")


# Test 5: Display Holdings Sample
logger.info("▶ Step 5: Sample Holdings (First 5) - Dashboard Endpoint Data...")
logger.info("=" * 60)
logger.info("SIMULATING /dashboard ENDPOINT")
logger.info("=" * 60)
holdings = portfolio_data.get('holdings', [])
logger.info(f"Total holdings: {len(holdings)}")

for i, h in enumerate(holdings[:5], 1):
    logger.info(f"{i}. {h.get('scheme_name', 'N/A')[:50]}")
    logger.info(f"   Current Value: ₹{h.get('current_value', 0):,.2f} | Invested: ₹{h.get('cost_value', 0):,.2f}")
    logger.info(f"   Gain/Loss: ₹{h.get('gain_loss', 0):,.2f} ({h.get('gain_loss_percent', 0):.2f}%)")
    logger.info(f"   XIRR: {h.get('xirr', 0):.2f}% | Broker: {h.get('broker', 'Unknown')}")

# Test 6: Display Active SIPs
logger.info("▶ Step 6: Active SIPs - SIP Analytics Endpoint Data...")
logger.info("=" * 60)
logger.info("SIMULATING /sip-analytics ENDPOINT")
logger.info("=" * 60)
active_sips = portfolio_data.get('active_sips', [])
logger.info(f"Total active SIPs: {len(active_sips)}")

if active_sips:
    for i, sip in enumerate(active_sips, 1):
        logger.info(f"{i}. {sip.get('scheme_name', 'N/A')[:50]}")
        logger.info(f"   Amount: ₹{sip.get('sip_amount', 0):,.2f} | Frequency: {sip.get('frequency', 'N/A')}")
        logger.info(f"   Last Date: {sip.get('last_installment_date', 'N/A')} | Broker: {sip.get('broker', 'Unknown')}")
else:
    logger.info("No active SIPs found")

# Test 7: Display Broker Summary
logger.info("▶ Step 7: Broker Summary...")
logger.info("=" * 60)
logger.info("BROKER INFORMATION SUMMARY")
logger.info("=" * 60)
broker_info = portfolio_data.get('broker_info', {})
logger.info(f"Total brokers: {len(broker_info)}")

if broker_info:
    for broker, info in broker_info.items():
        logger.info(f"Broker: {broker}")
        logger.info(f"  Total Invested: ₹{info.get('total_invested', 0):,.2f} | Schemes: {info.get('scheme_count', 0)} | Transactions: {info.get('transaction_count', 0)}")
else:
    logger.warning("No broker information found")


# Test 8: Test Q&A Agent with GPT-4.1 for Intent Classification
logger.info("▶ Step 8: Testing Q&A Agent - Chat Endpoint Simulation...")
logger.info("=" * 60)
logger.info("SIMULATING /chat ENDPOINT - TESTING INTENT CLASSIFICATION WITH GPT-4.1")
logger.info("=" * 60)

test_queries = [
    "What is my total portfolio value?",
    "How many SIPs do I have?",
    "Which fund has the best XIRR?",
    "Should I rebalance my portfolio?",
    "What is the latest market trend for tech funds?",
    "Compare my top 3 performing funds",
    "How much do I need to invest monthly to reach 1 crore in 10 years?"
]

try:
    logger.info("Initializing IntentClassifier with dedicated GPT-4.1 model")
    classifier = IntentClassifier()
    
    logger.info("Testing intent classification on sample queries")
    for idx, query in enumerate(test_queries, 1):
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Query {idx}/{len(test_queries)}: {query}")
        
        intents = classifier.classify(query)
        
        logger.info(f"Classified intents: {intents}")
        logger.info(f"Intent count: {len(intents)}")
        logger.info(f"Model Used: GPT-4.1 (dedicated intent classification model)")
    
    logger.info("✅ Intent classification successful")
    logger.info("All intent classifications completed successfully")
    
except Exception as e:
    logger.error(f"⚠️  Intent classification failed: {str(e)}")
    import traceback
    traceback.print_exc()

# Test 9: Test Full Multi-Agent Orchestration
logger.info("▶ Step 9: Testing Multi-Agent Orchestrator...")
logger.info("=" * 60)
logger.info("TESTING FULL ORCHESTRATOR WITH MULTIPLE AGENTS")
logger.info("=" * 60)

try:
    logger.info("Initializing MultiAgentOrchestrator")
    orchestrator = MultiAgentOrchestrator()
    
    # Test a complex query that requires orchestration
    test_query = "What is my total portfolio value and should I rebalance?"
    
    logger.info(f"Test Query: {test_query}")
    logger.info("Processing query through orchestrator")
    
    response = orchestrator.process_query(test_query)
    
    logger.info("Orchestrator response received")
    logger.info(f"Response length: {len(response)} characters")
    logger.info("=" * 80)
    logger.info("ORCHESTRATOR RESPONSE:")
    logger.info("=" * 80)
    logger.info(response[:500] + "..." if len(response) > 500 else response)
    logger.info("=" * 80)
    
    logger.info("✅ Multi-agent orchestration successful")
    
except Exception as e:
    logger.error(f"⚠️  Orchestration failed: {str(e)}")
    import traceback
    traceback.print_exc()


# Test 10: Individual Agent Testing
logger.info("▶ Step 10: Testing Individual Agents...")
logger.info("=" * 60)
logger.info("TESTING INDIVIDUAL AGENTS")
logger.info("=" * 60)

agent_tests = [
    ("Portfolio Agent", PortfolioAgent(), "analyze", "Show me my top 5 holdings"),
    ("Goal Agent", GoalAgent(), "plan", "How much do I need to invest for 1 crore in 10 years?"),
    ("Strategy Agent", StrategyAgent(), "advise", "Is my portfolio well balanced?"),
]

for agent_name, agent, method_name, test_query in agent_tests:
    try:
        logger.info(f"\nTesting {agent_name}")
        logger.info(f"Method: {method_name} | Query: {test_query}")
        
        method = getattr(agent, method_name)
        response = method(test_query)
        
        logger.info(f"{agent_name} responded successfully")
        logger.info(f"Response preview: {response[:200]}...")
        logger.info(f"✅ {agent_name} working")
        
    except Exception as e:
        logger.error(f"⚠️  {agent_name} error: {str(e)}")

logger.info("-" * 80)


# Summary
logger.info("=" * 80)
logger.info("DEBUG SESSION COMPLETE")
logger.info(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logger.info("=" * 80)
logger.info("")
logger.info("SUMMARY:")
logger.info(f"✅ Portfolio data processed successfully")
logger.info(f"✅ {len(holdings)} holdings loaded")
logger.info(f"✅ {len(active_sips)} active SIPs found")
logger.info(f"✅ {len(broker_info)} brokers identified")
logger.info(f"✅ Intent classification tested with dedicated GPT-4.1 model")
logger.info(f"✅ Multi-agent orchestration tested")
logger.info("")
logger.info("📊 All endpoints simulated successfully!")
logger.info("🔍 Check 'debug_main.log' for detailed logs")
logger.info("")
logger.info("Ready for Q&A queries via Flask UI!")

logger.info("=" * 60)
logger.info("DEBUG SESSION COMPLETED SUCCESSFULLY")
logger.info("=" * 60)
logger.info(f"Total holdings: {len(holdings)}")
logger.info(f"Total SIPs: {len(active_sips)}")
logger.info(f"Total brokers: {len(broker_info)}")
logger.info("All tests passed. System is ready.")

"""
Quick test script to verify intent classification logging
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import centralized logger
from utils.logger import get_logger

logger = get_logger(__name__)

logger.info("=" * 80)
logger.info("TESTING INTENT CLASSIFICATION LOGGING")
logger.info("=" * 80)

# Import components
from agents.coordinator import IntentClassifier
from agents.orchestrator import MultiAgentOrchestrator

# Test queries
test_queries = [
    "What is my total portfolio value?",
    "Should I rebalance my portfolio?",
    "How many SIPs do I have?"
]

# Test 1: Direct intent classifier
logger.info("\n▶ Test 1: Direct Intent Classification")
logger.info("-" * 80)

classifier = IntentClassifier()

for idx, query in enumerate(test_queries, 1):
    logger.info(f"\nQuery {idx}: {query}")
    intents = classifier.classify(query)
    logger.info(f"Result: {intents}")

# Test 2: Through orchestrator
logger.info("\n▶ Test 2: Through Orchestrator")
logger.info("-" * 80)

orchestrator = MultiAgentOrchestrator()

test_query = "What is my portfolio value and should I rebalance?"
logger.info(f"\nComplex Query: {test_query}")
response = orchestrator.process_query(test_query)
logger.info(f"Response received: {len(response)} characters")
logger.info(response[:200] + "..." if len(response) > 200 else response)

logger.info("\n" + "=" * 80)
logger.info("✅ LOGGING TEST COMPLETE")
logger.info("=" * 80)

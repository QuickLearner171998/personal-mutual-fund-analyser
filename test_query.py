"""
Quick Q&A Query Tester
Run with: python test_query.py "My current SIP"
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger
from agents.orchestrator import MultiAgentOrchestrator

logger = get_logger(__name__)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_query.py \"Your query here\"")
        print("Example: python test_query.py \"My current SIP\"")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    
    logger.info("=" * 80)
    logger.info(f"TESTING QUERY: {query}")
    logger.info("=" * 80)
    
    try:
        orchestrator = MultiAgentOrchestrator()
        response = orchestrator.process_query(query)
        
        print("\n" + "=" * 80)
        print("RESPONSE:")
        print("=" * 80)
        print(response)
        print("=" * 80)
        print(f"\nStats: {len(response)} chars, {len(response.split())} words")
        
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        import traceback
        traceback.print_exc()

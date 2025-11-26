"""
Multi-Agent Orchestrator
Coordinates multiple agents to answer complex queries
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.coordinator import IntentClassifier
from agents.portfolio_agent import PortfolioAgent
from agents.goal_agent import GoalAgent
from agents.market_agent import MarketAgent
from agents.strategy_agent import StrategyAgent
from agents.comparison_agent import ComparisonAgent
from typing import Iterator, Union
from utils.logger import get_logger

logger = get_logger(__name__)

class MultiAgentOrchestrator:
    def __init__(self):
        logger.info("Initializing MultiAgentOrchestrator")
        self.classifier = IntentClassifier()
        self.agents = {
            'portfolio': PortfolioAgent(),
            'goal': GoalAgent(),
            'market': MarketAgent(),
            'strategy': StrategyAgent(),
            'comparison': ComparisonAgent()
        }
        logger.info(f"Initialized {len(self.agents)} agents: {list(self.agents.keys())}")
    
    def process_query(self, query: str, stream: bool = False) -> Union[str, Iterator]:
        """
        Process user query through multi-agent system with error handling
        
        Args:
            query: User's question
            stream: Whether to stream response
        
        Returns:
            Agent response (string or iterator if streaming)
        """
        logger.info("=" * 60)
        logger.info("PROCESSING NEW QUERY")
        logger.info("=" * 60)
        logger.info(f"Query: '{query}'")
        logger.info(f"Stream mode: {stream}")
        
        try:
            # Step 1: Classify intent
            logger.info("Step 1: Classifying intent with dedicated GPT-4.1 model")
            intents = self.classifier.classify(query)
            logger.info(f"Classified intents: {intents}")
            
            # Step 2: Route to appropriate agent(s)
            if len(intents) == 1:
                # Single agent
                intent = intents[0]
                logger.info(f"Step 2: Routing to single agent: '{intent}'")
                agent = self.agents.get(intent)
                
                if not agent:
                    logger.error(f"Agent for intent '{intent}' not found")
                    return f"⚠️ Agent for '{intent}' not found. Please try rephrasing your question."
                
                try:
                    logger.info(f"Invoking {intent} agent")
                    if intent == 'portfolio':
                        response = agent.analyze(query, stream)
                    elif intent == 'goal':
                        response = agent.plan(query, stream)
                    elif intent == 'market':
                        response = agent.research(query, stream)
                    elif intent == 'strategy':
                        response = agent.advise(query, stream)
                    elif intent == 'comparison':
                        response = agent.compare([], stream)
                    
                    logger.info(f"Successfully received response from {intent} agent")
                    return response
                    
                except Exception as e:
                    logger.error(f"Error in {intent} agent: {str(e)}")
                    return f"⚠️ Error in {intent} agent: {str(e)}\n\nPlease try a different question or check if your portfolio data is loaded."
            
            else:
                # Multiple agents needed - run sequentially and synthesize
                logger.info(f"Step 2: Routing to multiple agents: {intents}")
                responses = []
                
                for intent in intents:
                    logger.info(f"Processing intent: '{intent}'")
                    agent = self.agents.get(intent)
                    
                    if not agent:
                        logger.warning(f"Agent for intent '{intent}' not found, skipping")
                        continue
                    
                    try:
                        logger.info(f"Invoking {intent} agent")
                        if intent == 'portfolio':
                            responses.append(("Portfolio Analysis", agent.analyze(query)))
                        elif intent == 'goal':
                            responses.append(("Goal Planning", agent.plan(query)))
                        elif intent == 'market':
                            responses.append(("Market Research", agent.research(query)))
                        elif intent == 'strategy':
                            responses.append(("Strategy Advice", agent.advise(query)))
                        elif intent == 'comparison':
                            responses.append(("Fund Comparison", agent.compare([])))
                        
                        logger.info(f"Successfully received response from {intent} agent")
                        
                    except Exception as e:
                        logger.error(f"Error in {intent} agent: {str(e)}")
                        responses.append((f"{intent.title()} Agent", f"⚠️ Error: {str(e)}"))
                
                if not responses:
                    logger.error("No responses received from any agent")
                    return "⚠️ Unable to process your query. Please try rephrasing or upload your CAS data first."
                
                # Combine responses
                logger.info(f"Combining {len(responses)} responses")
                combined = "\n\n".join([f"**{title}:**\n{resp}" for title, resp in responses])
                logger.info("Successfully combined all responses")
                return combined
                
        except Exception as e:
            logger.error(f"System error in orchestrator: {str(e)}")
            return f"⚠️ System error: {str(e)}\n\nPlease try again or contact support if the issue persists."


# Global instance
orchestrator = MultiAgentOrchestrator()


def answer_query(query: str, stream: bool = False):
    """Convenience function to answer queries"""
    return orchestrator.process_query(query, stream)


# Test
if __name__ == "__main__":
    orchestrator = MultiAgentOrchestrator()
    
    # Test single intent
    response = orchestrator.process_query("What is my total portfolio value?")
    logger.info(f"Response received: {len(response)} characters")
    
    logger.info("\n" + "="*50 + "\n")
    
    # Test multiple intents
    response = orchestrator.process_query("Show my portfolio and suggest if I should rebalance")
    logger.info(f"Response received: {len(response)} characters")

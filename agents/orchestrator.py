"""
Multi-Agent Orchestrator
Coordinates multiple agents to answer complex queries
"""
from agents.coordinator import IntentClassifier
from agents.portfolio_agent import PortfolioAgent
from agents.goal_agent import GoalAgent
from agents.market_agent import MarketAgent
from agents.strategy_agent import StrategyAgent
from agents.comparison_agent import ComparisonAgent
from typing import Iterator, Union

class MultiAgentOrchestrator:
    def __init__(self):
        self.classifier = IntentClassifier()
        self.agents = {
            'portfolio': PortfolioAgent(),
            'goal': GoalAgent(),
            'market': MarketAgent(),
            'strategy': StrategyAgent(),
            'comparison': ComparisonAgent()
        }
    
    def process_query(self, query: str, stream: bool = False) -> Union[str, Iterator]:
        """
        Process user query through multi-agent system with error handling
        
        Args:
            query: User's question
            stream: Whether to stream response
        
        Returns:
            Agent response (string or iterator if streaming)
        """
        try:
            # Step 1: Classify intent
            intents = self.classifier.classify(query)
            
            # Step 2: Route to appropriate agent(s)
            if len(intents) == 1:
                # Single agent
                intent = intents[0]
                agent = self.agents.get(intent)
                
                if not agent:
                    return f"⚠️ Agent for '{intent}' not found. Please try rephrasing your question."
                
                try:
                    if intent == 'portfolio':
                        return agent.analyze(query, stream)
                    elif intent == 'goal':
                        return agent.plan(query, stream)
                    elif intent == 'market':
                        return agent.research(query, stream)
                    elif intent == 'strategy':
                        return agent.advise(query, stream)
                    elif intent == 'comparison':
                        return agent.compare([], stream)
                except Exception as e:
                    return f"⚠️ Error in {intent} agent: {str(e)}\n\nPlease try a different question or check if your portfolio data is loaded."
            
            else:
                # Multiple agents needed - run sequentially and synthesize
                responses = []
                for intent in intents:
                    agent = self.agents.get(intent)
                    
                    if not agent:
                        continue
                    
                    try:
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
                    except Exception as e:
                        responses.append((f"{intent.title()} Agent", f"⚠️ Error: {str(e)}"))
                
                if not responses:
                    return "⚠️ Unable to process your query. Please try rephrasing or upload your CAS data first."
                
                # Combine responses
                combined = "\n\n".join([f"**{title}:**\n{resp}" for title, resp in responses])
                return combined
                
        except Exception as e:
            return f"⚠️ System error: {str(e)}\n\nPlease try again or contact support if the issue persists."


# Global instance
orchestrator = MultiAgentOrchestrator()


def answer_query(query: str, stream: bool = False):
    """Convenience function to answer queries"""
    return orchestrator.process_query(query, stream)


# Test
if __name__ == "__main__":
    # Test single intent
    response = answer_query("What is my total portfolio value?")
    print(response)
    
    print("\n" + "="*50 + "\n")
    
    # Test multiple intents
    response = answer_query("Show my portfolio and suggest if I should rebalance")
    print(response)

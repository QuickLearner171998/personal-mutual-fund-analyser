"""
Strategy Advisor Agent
Provides investment strategy, rebalancing, and risk advice
"""
from llm.llm_wrapper import invoke_llm
from llm.prompts import get_agent_prompt
from database.json_store import PortfolioStore
import config
import json

class StrategyAgent:
    def __init__(self):
        self.store = PortfolioStore()
    
    def advise(self, query: str, stream: bool = False):
        """
        Provide strategic investment advice
        
        Args:
            query: Strategy question
            stream: Whether to stream response
        """
        # Load portfolio for context
        portfolio = self.store.get_portfolio()
        
        if not portfolio:
            return "⚠️ No portfolio data found. Please upload your CAS PDF first."
        
        # Prepare portfolio data
        portfolio_data = {
            'total_value': portfolio.get('total_value'),
            'allocation': portfolio.get('allocation'),
            'holdings': portfolio.get('holdings', []),
            'xirr': portfolio.get('xirr')
        }
        
        # Build prompt
        prompt = get_agent_prompt(
            'strategy',
            portfolio_data=json.dumps(portfolio_data, indent=2, default=str),
            query=query
        )
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        # Use gpt-5-mini with medium reasoning
        return invoke_llm(
            config.STRATEGY_LLM_MODEL,
            messages,
            max_tokens=config.STRATEGY_MAX_TOKENS,
            timeout=config.STRATEGY_TIMEOUT,
            reasoning_effort="medium",
            stream=stream
        )


# Test
if __name__ == "__main__":
    agent = StrategyAgent()
    response = agent.advise("Should I rebalance my portfolio?")
    print(response)

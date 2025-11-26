"""
Goal Planning Agent
Helps with SIP calculations, goal tracking, and future planning
"""
from llm.llm_wrapper import invoke_llm
from llm.prompts import get_agent_prompt
from database.json_store import PortfolioStore
import config
import json

class GoalAgent:
    def __init__(self):
        self.store = PortfolioStore()
    
    def plan(self, query: str, stream: bool = False):
        """
        Help with goal planning
        
        Args:
            query: User's goal/question
            stream: Whether to stream response
        """
        # Load portfolio context (optional, for progress tracking)
        portfolio = self.store.get_portfolio()
        
        portfolio_context = {
            'current_value': portfolio.get('total_value', 0) if portfolio else 0,
            'monthly_sip': self._estimate_current_sip(portfolio) if portfolio else 0
        }
        
        # Build prompt
        prompt = get_agent_prompt(
            'goal',
            portfolio_data=json.dumps(portfolio_context, indent=2),
            query=query
        )
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        # Use gpt-5-mini with medium reasoning
        return invoke_llm(
            config.GOAL_LLM_MODEL,
            messages,
            max_tokens=config.GOAL_MAX_TOKENS,
            timeout=config.GOAL_TIMEOUT,
            reasoning_effort="medium",
            stream=stream
        )
    
    def _estimate_current_sip(self, portfolio):
        """Estimate current monthly SIP from transactions"""
        # TODO: Analyze transactions to find SIP amount
        return 0


# Test
if __name__ == "__main__":
    agent = GoalAgent()
    response = agent.plan("How much SIP do I need to reach ₹1 crore in 15 years?")
    print(response)

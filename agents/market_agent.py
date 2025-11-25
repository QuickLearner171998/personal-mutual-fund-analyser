"""
Market Research Agent
Uses Perplexity for real-time market data and fund research
"""
from llm.llm_wrapper import invoke_llm
from llm.prompts import get_agent_prompt
from external.perplexity_client import perplexity

class MarketAgent:
    def __init__(self):
        self.perplexity = perplexity
    
    def research(self, query: str, stream: bool = False):
        """
        Research market data using Perplexity
        
        Args:
            query: Market research query
            stream: Whether to stream response
        """
        # Use Perplexity for real-time search
        print(f"🔍 Researching: {query}")
        perplexity_result = self.perplexity.search(query)
        
        if not perplexity_result['success']:
            return f"⚠️ Unable to fetch real-time data: {perplexity_result['answer']}"
        
        # Build structured response
        answer = perplexity_result['answer']
        citations = perplexity_result.get('citations', [])
        
        response = f"{answer}\n\n"
        
        if citations:
            response += "**Sources:**\n"
            for i, citation in enumerate(citations[:5], 1):
                response += f"{i}. {citation}\n"
        
        return response


# Test
if __name__ == "__main__":
    agent = MarketAgent()
    response = agent.research("What is the current NAV of HDFC Flexi Cap Fund?")
    print(response)

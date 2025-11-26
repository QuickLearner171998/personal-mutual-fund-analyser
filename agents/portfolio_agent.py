from llm.llm_wrapper import invoke_llm
from llm.prompts import get_agent_prompt
from database.json_store import PortfolioStore
from vector_db.faiss_store import LocalVectorStore
import config
import json

class PortfolioAgent:
    def __init__(self):
        self.store = PortfolioStore()
        self.vector_store = LocalVectorStore()
    
    def analyze(self, query: str, stream: bool = False):
        """
        Analyze portfolio based on query with RAG support
        
        Args:
            query: User's question
            stream: Whether to stream response
        
        Returns:
            Agent response (string or iterator if streaming)
        """
        # Load portfolio data
        portfolio = self.store.get_portfolio()
        
        if not portfolio:
            return "⚠️ No portfolio data found. Please upload your CAS PDF first."
        
        # Use FAISS for semantic search if query is complex
        rag_context = ""
        try:
            search_results = self.vector_store.search(query, k=3)
            if search_results:
                rag_context = "\n**Relevant context from portfolio:**\n"
                for result in search_results:
                    metadata = result.get('metadata', {})
                    if metadata.get('type') == 'holding':
                        rag_context += f"- {metadata.get('scheme_name', 'Unknown')}\n"
        except Exception as e:
            print(f"RAG search failed: {e}")
        
        # Prepare portfolio data
        portfolio_summary = {
            'total_value': portfolio.get('total_value'),
            'total_invested': portfolio.get('total_invested'),
            'total_gain': portfolio.get('total_gain'),
            'total_gain_percent': portfolio.get('total_gain_percent'),
            'xirr': portfolio.get('xirr'),
            'allocation': portfolio.get('allocation'),
            'num_funds': len(portfolio.get('holdings', [])),
            'top_5_holdings': self._get_top_holdings(portfolio, 5),
            'all_holdings': portfolio.get('holdings', [])[:10]  # Limit for prompt size
        }
        
        # Build prompt with RAG context
        prompt = get_agent_prompt(
            'portfolio',
            portfolio_data=json.dumps(portfolio_summary, indent=2, default=str),
            query=query + rag_context
        )
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        # Use RAG model (gpt-4o-mini) for portfolio queries
        return invoke_llm(
            config.PORTFOLIO_LLM_MODEL,
            messages,
            max_tokens=config.PORTFOLIO_MAX_TOKENS,
            timeout=config.PORTFOLIO_TIMEOUT,
            stream=stream
        )
    
    def _get_top_holdings(self, portfolio, n=5):
        """Get top N holdings by value"""
        holdings = portfolio.get('holdings', [])
        sorted_holdings = sorted(holdings, key=lambda x: x.get('current_value', 0), reverse=True)
        
        return [{
            'scheme_name': h.get('scheme_name'),
            'current_value': h.get('current_value'),
            'gain_loss': h.get('current_value', 0) - h.get('invested_value', 0),
            'allocation_pct': (h.get('current_value', 0) / portfolio.get('total_value', 1)) * 100
        } for h in sorted_holdings[:n]]


# Test
if __name__ == "__main__":
    agent = PortfolioAgent()
    response = agent.analyze("What are my top 3 holdings?")
    print(response)

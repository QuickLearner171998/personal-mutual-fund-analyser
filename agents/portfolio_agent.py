from llm.llm_wrapper import invoke_llm
from llm.prompts import get_agent_prompt
from database.json_store import PortfolioStore
from agents.rag_service import RAGService
import config
import json

class PortfolioAgent:
    def __init__(self):
        self.store = PortfolioStore()
        self.rag_service = RAGService()
    
    def analyze(self, query: str, stream: bool = False):
        """
        Analyze portfolio based on query with RAG support.
        Uses RAG service for query understanding and raw data retrieval.
        Uses gpt-4.1 for final response synthesis.
        
        Args:
            query: User's question
            stream: Whether to stream response
        
        Returns:
            Agent response (string or iterator if streaming)
        """
        # Check if portfolio data exists
        portfolio = self.store.get_portfolio()
        if not portfolio:
            return "⚠️ No portfolio data found. Please upload your data files first."
        
        # Use RAG service to get context (o3-mini for query understanding)
        try:
            rag_context = self.rag_service.get_context_for_query(query, k=15)
        except Exception as e:
            print(f"RAG service failed: {e}")
            # Fallback to basic response
            return f"I encountered an error processing your query: {str(e)}"
        
        # Prepare context data for LLM
        context_data = self._format_context_for_llm(rag_context)
        
        # Build concise prompt
        prompt = get_agent_prompt(
            'concise_qna',
            query=query,
            context_data=json.dumps(context_data, indent=2, default=str)
        )
        
        messages = [{"role": "user", "content": prompt}]
        
        # Use gpt-4.1 for response synthesis (upgraded from gpt-4.1-mini)
        return invoke_llm(
            "gpt-4.1",  # Using gpt-4.1 for better synthesis
            messages,
            max_tokens=2000,  # Shorter responses
            timeout=60,
            stream=stream
        )
    
    def _format_context_for_llm(self, rag_context: dict) -> dict:
        """
        Format RAG context into clean structure for LLM.
        Returns only the essential data without extra processing.
        """
        query_type = rag_context.get('query_type', 'summary')
        formatted = {
            'query_type': query_type,
            'focus': rag_context.get('focus', '')
        }
        
        # Add relevant data based on query type
        if query_type == 'sip':
            sips = rag_context.get('sips', [])
            formatted['sips'] = [{
                'scheme_name': s.get('scheme_name', ''),
                'sip_amount': s.get('sip_amount', 0),
                'frequency': s.get('frequency', 'Monthly'),
                'last_installment_date': s.get('last_installment_date', ''),
                'total_invested': s.get('total_invested', 0),
                'broker': s.get('broker', 'Direct'),
                'is_active': s.get('is_active', False)
            } for s in sips]
            formatted['count'] = len(sips)
        
        elif query_type == 'holdings':
            holdings = rag_context.get('holdings', [])
            formatted['holdings'] = [{
                'scheme_name': h.get('scheme_name', ''),
                'current_value': h.get('current_value', 0),
                'cost_value': h.get('cost_value', 0),
                'gain_loss': h.get('current_value', 0) - h.get('cost_value', 0),
                'gain_loss_percent': h.get('gain_loss_percent', 0),
                'xirr': h.get('xirr', 0),
                'type': h.get('type', 'EQUITY')
            } for h in holdings]
            formatted['count'] = len(holdings)
        
        elif query_type == 'summary':
            formatted['summary'] = rag_context.get('summary', {})
        
        elif query_type == 'specific_fund':
            formatted['holdings'] = rag_context.get('holdings', [])
            formatted['sips'] = rag_context.get('sips', [])
        
        return formatted


# Test
if __name__ == "__main__":
    agent = PortfolioAgent()
    response = agent.analyze("What are my current active SIPs?")
    print(response)

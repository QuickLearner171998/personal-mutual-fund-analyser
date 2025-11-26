"""
RAG Service for Portfolio Q&A
Centralized service using o3-mini for query understanding and raw data retrieval
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Dict, List, Optional
import json
from database.json_store import PortfolioStore
from vector_db.faiss_store import LocalVectorStore
from llm.llm_wrapper import invoke_llm
import config


class RAGService:
    """
    Centralized RAG service for portfolio queries.
    Uses o3-mini for query understanding and retrieval orchestration.
    Returns raw, unprocessed data for LLM synthesis.
    """
    
    def __init__(self):
        self.store = PortfolioStore()
        self.vector_store = LocalVectorStore()
    
    def analyze_query(self, query: str) -> Dict:
        """
        Use o3-mini to understand query intent and extract parameters.
        
        Returns:
            query_type: 'sip', 'holdings', 'summary', 'performance', 'specific_fund'
            filters: dict of metadata filters
            focus: what the user is asking about
        """
        analysis_prompt = f"""Analyze this mutual fund portfolio query and extract:
1. Query Type: sip / holdings / summary / performance / specific_fund / broker / allocation
2. Filters needed (if any): active_only, fund_category, specific_fund_name, broker_name
3. Focus: concise description of what user wants

Query: "{query}"

Respond in JSON format:
{{
    "query_type": "...",
    "filters": {{}},
    "focus": "..."
}}

Examples:
- "My current SIP" -> {{"query_type": "sip", "filters": {{"active_only": true}}, "focus": "list of active SIPs"}}
- "Top 5 holdings" -> {{"query_type": "holdings", "filters": {{"limit": 5, "sort": "value_desc"}}, "focus": "top holdings by value"}}
- "HDFC funds" -> {{"query_type": "specific_fund", "filters": {{"fund_name": "HDFC"}}, "focus": "all HDFC funds"}}
"""
        
        messages = [{"role": "user", "content": analysis_prompt}]
        
        # Use o3-mini for query understanding
        response = invoke_llm(
            "o3-mini",
            messages,
            max_tokens=500,
            timeout=30
        )
        
        try:
            # Parse JSON response
            analysis = json.loads(response.strip())
            return analysis
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "query_type": "summary",
                "filters": {},
                "focus": query
            }
    
    def retrieve_relevant_data(self, query: str, query_analysis: Dict, k: int = 10) -> Dict:
        """
        Retrieve relevant raw data based on query analysis.
        
        Args:
            query: Original user query
            query_analysis: Analysis from analyze_query()
            k: Number of semantic search results
        
        Returns:
            Dict with raw portfolio data relevant to query
        """
        query_type = query_analysis.get('query_type', 'summary')
        filters = query_analysis.get('filters', {})
        
        # Get all raw data from store
        portfolio = self.store.get_portfolio()
        if not portfolio:
            return {"error": "No portfolio data found"}
        
        # Perform semantic search via FAISS
        search_results = self.vector_store.search(query, k=k)
        
        # Extract raw data based on query type and filters
        result = {
            "query_type": query_type,
            "focus": query_analysis.get('focus', query)
        }
        
        if query_type == 'sip':
            # Get SIPs from search results or all SIPs
            sips = []
            for res in search_results:
                if res['metadata'].get('type') == 'sip':
                    sip_data = json.loads(res['metadata']['data'])
                    # Apply filters
                    if filters.get('active_only') and not sip_data.get('is_active'):
                        continue
                    sips.append(sip_data)
            
            # If no SIPs from search, get all from portfolio
            if not sips:
                sips = portfolio.get('active_sips', [])
                if filters.get('active_only'):
                    sips = [s for s in sips if s.get('is_active', False)]
            
            result['sips'] = sips
            result['count'] = len(sips)
        
        elif query_type == 'holdings':
            # Get holdings from search results
            holdings = []
            for res in search_results:
                if res['metadata'].get('type') == 'holding':
                    holding_data = json.loads(res['metadata']['data'])
                    # Apply filters
                    if filters.get('fund_category') and holding_data.get('type') != filters['fund_category']:
                        continue
                    holdings.append(holding_data)
            
            # If no holdings from search, get all
            if not holdings:
                holdings = portfolio.get('holdings', [])
            
            # Sort and limit
            if filters.get('sort') == 'value_desc':
                holdings = sorted(holdings, key=lambda x: x.get('current_value', 0), reverse=True)
            
            if filters.get('limit'):
                holdings = holdings[:filters['limit']]
            
            result['holdings'] = holdings
            result['count'] = len(holdings)
        
        elif query_type == 'specific_fund':
            # Search for specific fund
            fund_name = filters.get('fund_name', '')
            holdings = []
            sips = []
            
            for res in search_results:
                metadata = res['metadata']
                if metadata.get('type') == 'holding':
                    holding_data = json.loads(metadata['data'])
                    if fund_name.lower() in holding_data.get('scheme_name', '').lower():
                        holdings.append(holding_data)
                elif metadata.get('type') == 'sip':
                    sip_data = json.loads(metadata['data'])
                    if fund_name.lower() in sip_data.get('scheme_name', '').lower():
                        sips.append(sip_data)
            
            result['holdings'] = holdings
            result['sips'] = sips
        
        elif query_type == 'summary':
            # Return portfolio summary
            result['summary'] = {
                'total_value': portfolio.get('total_value', 0),
                'total_invested': portfolio.get('total_invested', 0),
                'total_gain': portfolio.get('total_gain', 0),
                'total_gain_percent': portfolio.get('total_gain_percent', 0),
                'xirr': portfolio.get('xirr', 0),
                'num_funds': portfolio.get('num_funds', 0),
                'num_active_sips': portfolio.get('num_active_sips', 0)
            }
        
        else:
            # Default: return top search results
            result['search_results'] = search_results[:5]
        
        return result
    
    def get_context_for_query(self, query: str, k: int = 10) -> Dict:
        """
        Complete RAG pipeline: analyze query -> retrieve data -> return context
        
        Args:
            query: User's question
            k: Number of semantic search results
        
        Returns:
            Dict with query analysis and relevant raw data
        """
        # Step 1: Analyze query using o3-mini
        query_analysis = self.analyze_query(query)
        
        # Step 2: Retrieve relevant raw data
        context = self.retrieve_relevant_data(query, query_analysis, k=k)
        
        # Add query analysis to context
        context['query_analysis'] = query_analysis
        context['original_query'] = query
        
        return context


# Global instance
rag_service = RAGService()


def get_rag_context(query: str, k: int = 10) -> Dict:
    """Convenience function to get RAG context"""
    return rag_service.get_context_for_query(query, k=k)


if __name__ == "__main__":
    # Test
    service = RAGService()
    
    # Test SIP query
    print("=" * 80)
    print("TEST: My current SIP")
    print("=" * 80)
    context = service.get_context_for_query("My current SIP")
    print(json.dumps(context.get('query_analysis'), indent=2))
    print(f"\nFound {context.get('count', 0)} SIPs")
    
    # Test holdings query
    print("\n" + "=" * 80)
    print("TEST: Top 5 holdings")
    print("=" * 80)
    context = service.get_context_for_query("What are my top 5 holdings?")
    print(json.dumps(context.get('query_analysis'), indent=2))
    print(f"\nFound {context.get('count', 0)} holdings")

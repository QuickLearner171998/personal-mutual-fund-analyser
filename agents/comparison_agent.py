"""
Fund Comparison Agent
Compares mutual funds using MFAPI and market research
"""
from llm.llm_wrapper import invoke_llm
from llm.prompts import get_agent_prompt
from enrichment.nav_fetcher import NAVFetcher
from external.perplexity_client import perplexity
import json

class ComparisonAgent:
    def __init__(self):
        self.nav_fetcher = NAVFetcher()
        self.perplexity = perplexity
    
    def compare(self, fund_names: list, stream: bool = False):
        """
        Compare multiple mutual funds
        
        Args:
            fund_names: List of fund names to compare
            stream: Whether to stream response
        """
        if not fund_names or len(fund_names) < 2:
            return "⚠️ Please provide at least 2 fund names to compare."
        
        # Fetch fund data from MFAPI
        fund_data = {}
        for fund_name in fund_names:
            # Search for fund
            search_results = self.nav_fetcher.search_fund(fund_name)
            
            if search_results:
                best_match = search_results[0]
                fund_data[fund_name] = best_match
        
        if len(fund_data) < 2:
            # Use Perplexity for comparison
            query = f"Compare {' vs '.join(fund_names)} mutual funds in India"
            result = self.perplexity.search(query)
            return result.get('answer', 'Unable to fetch comparison data')
        
        # Build structured comparison
        prompt = get_agent_prompt(
            'comparison',
            fund_names=', '.join(fund_names),
            fund_data=json.dumps(fund_data, indent=2)
        )
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        return invoke_llm(messages, stream=stream)

"""
Fund Comparison Agent
Compares mutual funds using Perplexity Sonar Pro for real-time data
"""
from external.perplexity_client import perplexity
from utils.logger import get_logger
import config

logger = get_logger(__name__)

class ComparisonAgent:
    def __init__(self):
        self.perplexity = perplexity
        logger.info(f"Comparison Agent initialized with {config.COMPARISON_LLM_MODEL}")
    
    def compare(self, fund_names: list, stream: bool = False):
        """
        Compare multiple mutual funds using Perplexity for real-time market data
        
        Args:
            fund_names: List of fund names to compare (or query string)
            stream: Whether to stream response (not supported for Perplexity)
        """
        # If fund_names is actually a query string, use it directly
        if isinstance(fund_names, str):
            query = fund_names
        elif not fund_names or len(fund_names) < 2:
            return "⚠️ Please provide at least 2 fund names to compare."
        else:
            query = f"Compare {' vs '.join(fund_names)} mutual funds in India. Provide detailed comparison of returns, expense ratios, risk profiles, and investment strategies."
        
        logger.info(f"Using Perplexity ({config.COMPARISON_LLM_MODEL}) for fund comparison")
        logger.info(f"Query: {query}")
        
        try:
            # Use Perplexity for real-time market research
            result = self.perplexity.search(query)
            
            if result.get('success'):
                response = result.get('answer', '')
                citations = result.get('citations', [])
                
                # Add citations to response
                if citations:
                    response += "\n\n**Sources:**\n"
                    for i, citation in enumerate(citations, 1):
                        response += f"{i}. {citation}\n"
                
                logger.info(f"Perplexity comparison completed successfully")
                return response
            else:
                logger.error("Perplexity search failed")
                return "⚠️ Unable to fetch comparison data. Please try again later."
                
        except Exception as e:
            logger.error(f"Error in comparison: {str(e)}")
            return f"⚠️ Error comparing funds: {str(e)}"

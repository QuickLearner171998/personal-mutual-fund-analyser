"""
Perplexity API Client for Market Research
Real-time financial news and trends
"""
import requests
from typing import Dict, List
import config

class PerplexityClient:
    def __init__(self):
        self.api_key = config.PERPLEXITY_API_KEY
        self.base_url = config.PERPLEXITY_BASE_URL
        self.timeout = config.PERPLEXITY_TIMEOUT
        
    def search(self, query: str, model: str = None) -> Dict:
        """
        Search using Perplexity API
        
        Args:
            query: Search query
            model: Perplexity model (online models have web access)
        
        Returns:
            {"answer": str, "citations": List[str]}
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model or config.PERPLEXITY_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a financial research assistant. Provide accurate, cited information about mutual funds, markets, and investments."
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                "temperature": config.PERPLEXITY_TEMPERATURE,
                "max_tokens": config.PERPLEXITY_MAX_TOKENS
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data['choices'][0]['message']['content']
                
                # Extract citations if available
                citations = data.get('citations', [])
                
                return {
                    "answer": answer,
                    "citations": citations,
                    "success": True
                }
            else:
                return {
                    "answer": f"Error: {response.status_code}",
                    "citations": [],
                    "success": False
                }
                
        except Exception as e:
            print(f"Perplexity API error: {str(e)}")
            return {
                "answer": f"Failed to fetch: {str(e)}",
                "citations": [],
                "success": False
            }
    
    def search_fund_news(self, fund_name: str) -> Dict:
        """Get latest news about a specific mutual fund"""
        query = f"Latest news and performance updates about {fund_name} mutual fund in India. Include NAV trends, fund manager changes, and any recent developments."
        return self.search(query)
    
    def search_market_trends(self) -> Dict:
        """Get current market trends"""
        query = "Current Indian mutual fund market trends, top performing categories, and investment outlook for the next quarter."
        return self.search(query)
    
    def analyze_fund_comparison(self, fund1: str, fund2: str) -> Dict:
        """Compare two mutual funds"""
        query = f"Compare {fund1} vs {fund2} mutual funds in India. Include performance, expense ratio, fund manager, and investment strategy."
        return self.search(query)


# Global instance
perplexity = PerplexityClient()


# Test
if __name__ == "__main__":
    result = perplexity.search("What is the current Nifty 50 performance?")
    print(f"Answer: {result['answer']}")
    print(f"Citations: {result['citations']}")

"""
Intent Classifier - Routes queries to appropriate agents
"""
from llm.llm_wrapper import invoke_llm
from typing import List, Dict

class IntentClassifier:
    def __init__(self):
        self.intents = {
            'portfolio': 'Questions about current holdings, allocation, performance, gains/losses',
            'goal': 'Future planning, SIP calculations, target corpus, retirement planning',
            'market': 'Latest fund news, market trends, fund research, real-time data',
            'comparison': 'Comparing different mutual funds',
            'strategy': 'Rebalancing, risk assessment, tax optimization, investment strategy'
        }
    
    def classify(self, query: str) -> List[str]:
        """
        Classify user query to one or more agent intents
        
        Returns:
            List of intents (can be multiple for complex queries)
        """
        intent_descriptions = "\n".join([f"- {k}: {v}" for k, v in self.intents.items()])
        
        messages = [
            {
                "role": "system",
                "content": f"""You are an intent classifier for a mutual fund portfolio Q&A system.

**Available Intents:**
{intent_descriptions}

**Your Task:**
Classify the user's query into one or more intents.
Output ONLY the intent names as a comma-separated list (e.g., "portfolio,strategy")
If multiple intents are needed, include all relevant ones.
"""
            },
            {
                "role": "user",
                "content": f"Query: {query}\n\nIntents:"
            }
        ]
        
        try:
            response = invoke_llm(messages)
            
            # Parse response (should be like "portfolio,strategy")
            intents = [intent.strip() for intent in response.split(',')]
            
            # Validate intents
            valid_intents = [i for i in intents if i in self.intents]
            
            # Default to portfolio if nothing matched
            if not valid_intents:
                valid_intents = ['portfolio']
            
            print(f"🎯 Classified query as: {', '.join(valid_intents)}")
            return valid_intents
            
        except Exception as e:
            print(f"Intent classification error: {e}, defaulting to 'portfolio'")
            return ['portfolio']


# Test
if __name__ == "__main__":
    classifier = IntentClassifier()
    
    test_queries = [
        "What is my current portfolio value?",
        "How much SIP do I need for ₹1 crore in 10 years?",
        "Compare HDFC Flexi Cap vs ICICI Bluechip",
        "Should I rebalance my portfolio?",
        "What's the latest news on SBI Small Cap Fund?"
    ]
    
    for q in test_queries:
        intents = classifier.classify(q)
        print(f"Q: {q}\nA: {intents}\n")

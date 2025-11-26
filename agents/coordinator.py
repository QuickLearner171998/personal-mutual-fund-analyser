"""
Intent Classifier - Routes queries to appropriate agents
Uses dedicated GPT-4.1 LLM for intent classification
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm.llm_wrapper import invoke_llm
from typing import List, Dict
from utils.logger import get_logger

logger = get_logger(__name__)

class IntentClassifier:
    def __init__(self):
        self.intents = {
            'portfolio': 'Questions about current holdings, allocation, performance, gains/losses',
            'goal': 'Future planning, SIP calculations, target corpus, retirement planning',
            'market': 'Latest fund news, market trends, fund research, real-time data',
            'comparison': 'Comparing different mutual funds',
            'strategy': 'Rebalancing, risk assessment, tax optimization, investment strategy'
        }
        logger.info("IntentClassifier initialized with dedicated GPT-4.1 model")
    
    def classify(self, query: str) -> List[str]:
        """
        Classify user query to one or more agent intents using dedicated GPT-4.1 LLM
        
        Args:
            query: User's question
        
        Returns:
            List of intents (can be multiple for complex queries)
        """
        logger.info(f"Classifying query: '{query}'")
        
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
            logger.info("Invoking dedicated Intent Classification LLM (GPT-4.1)")
            # Use use_intent=True to force dedicated intent classification model
            response = invoke_llm(messages, use_intent=True)
            
            logger.info(f"Intent LLM response: '{response}'")
            
            # Parse response (should be like "portfolio,strategy")
            intents = [intent.strip() for intent in response.split(',')]
            
            # Validate intents
            valid_intents = [i for i in intents if i in self.intents]
            
            # Default to portfolio if nothing matched
            if not valid_intents:
                logger.warning(f"No valid intents found in response: '{response}', defaulting to 'portfolio'")
                valid_intents = ['portfolio']
            
            logger.info(f"Classified intents: {', '.join(valid_intents)}")
            
            return valid_intents
            
        except Exception as e:
            logger.error(f"Intent classification error: {str(e)}, defaulting to 'portfolio'")
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
        logger.info(f"Query: {q} | Intents: {intents}")

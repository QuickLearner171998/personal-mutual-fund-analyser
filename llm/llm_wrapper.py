"""
LLM Wrapper with GPT-4o + Gemini Fallback
Unified interface for all LLM calls
"""
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from typing import List, Dict, Union, Iterator
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger
import config

logger = get_logger(__name__)

class LLMWrapper:
    def __init__(self):
        logger.info("Initializing LLM Wrapper")
        
        # Primary: gpt-5 (with reasoning)
        self.primary_llm = ChatOpenAI(
            model=config.PRIMARY_LLM_MODEL,
            api_key=config.OPENAI_API_KEY
        )
        logger.info(f"Primary LLM initialized: {config.PRIMARY_LLM_MODEL}")
        
        # RAG: gpt-4.1-mini (fast for simple queries)
        self.rag_llm = ChatOpenAI(
            model=config.RAG_LLM_MODEL,
            api_key=config.OPENAI_API_KEY
        )
        logger.info(f"RAG LLM initialized: {config.RAG_LLM_MODEL}")
        
        # Intent Classification: gpt-4.1-mini (dedicated for intent classification)
        self.intent_llm = ChatOpenAI(
            model=config.INTENT_CLASSIFICATION_MODEL,
            api_key=config.OPENAI_API_KEY
        )
        logger.info(f"Intent Classification LLM initialized: {config.INTENT_CLASSIFICATION_MODEL}")
        
        # Reasoning: gpt-5
        self.reasoning_llm = ChatOpenAI(
            model=config.REASONING_LLM_MODEL,
            api_key=config.OPENAI_API_KEY
        )
        logger.info(f"Reasoning LLM initialized: {config.REASONING_LLM_MODEL}")
        
        # Fallback: Gemini
        self.fallback_llm = ChatGoogleGenerativeAI(
            model=config.FALLBACK_LLM_MODEL,
            google_api_key=config.GOOGLE_API_KEY
        )
        logger.info(f"Fallback LLM initialized: {config.FALLBACK_LLM_MODEL}")
    
    def invoke(self, messages: List[Dict], use_reasoning: bool = False, use_rag: bool = False, use_intent: bool = False, stream: bool = False):
        """
        Invoke LLM with automatic fallback
        
        Args:
            messages: List of {"role": "system/user/assistant", "content": "..."}
            use_reasoning: Use o1-preview for advanced reasoning
            use_rag: Use fast gpt-4o-mini for simple RAG queries
            use_intent: Use dedicated intent classification model (GPT-4.1)
            stream: Stream response tokens
        """
        # Convert to LangChain format
        lc_messages = self._convert_messages(messages)
        
        # Choose model
        if use_intent:
            llm = self.intent_llm
            model_name = "Intent Classification"
            logger.info(f"Using Intent Classification LLM: {config.INTENT_CLASSIFICATION_MODEL}")
        elif use_reasoning:
            llm = self.reasoning_llm
            model_name = "Reasoning"
            logger.info(f"Using Reasoning LLM: {config.REASONING_LLM_MODEL}")
        elif use_rag:
            llm = self.rag_llm
            model_name = "RAG"
            logger.info(f"Using RAG LLM: {config.RAG_LLM_MODEL}")
        else:
            llm = self.primary_llm
            model_name = "Primary"
            logger.info(f"Using Primary LLM: {config.PRIMARY_LLM_MODEL}")
        
        try:
            if stream:
                logger.info(f"Streaming response from {model_name} LLM")
                return llm.stream(lc_messages)
            else:
                logger.info(f"Invoking {model_name} LLM")
                response = llm.invoke(lc_messages)
                logger.info(f"Successfully received response from {model_name} LLM")
                return response.content
                
        except Exception as e:
            logger.warning(f"{model_name} LLM failed: {str(e)}, falling back to Gemini")
            
            try:
                if stream:
                    logger.info("Streaming response from Fallback LLM (Gemini)")
                    return self.fallback_llm.stream(lc_messages)
                else:
                    logger.info("Invoking Fallback LLM (Gemini)")
                    response = self.fallback_llm.invoke(lc_messages)
                    logger.info("Successfully received response from Fallback LLM")
                    return response.content
            except Exception as e2:
                logger.error(f"Fallback LLM also failed: {str(e2)}")
                raise
    
    def _convert_messages(self, messages: List[Dict]) -> List:
        """Convert dict messages to LangChain message objects"""
        lc_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
        
        return lc_messages


# Global instance
llm = LLMWrapper()


def invoke_llm(messages: List[Dict], use_reasoning: bool = False, use_rag: bool = False, use_intent: bool = False, stream: bool = False):
    """Convenience function for LLM calls"""
    return llm.invoke(messages, use_reasoning, use_rag, use_intent, stream)


# Test
if __name__ == "__main__":
    logger.info("Testing LLM Wrapper")
    test_messages = [
        {"role": "system", "content": "You are a helpful financial advisor."},
        {"role": "user", "content": "What is XIRR?"}
    ]
    
    response = invoke_llm(test_messages)
    logger.info(f"Test response received: {len(response)} characters")

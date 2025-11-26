"""
LLM Wrapper with Multi-Model Support
Unified interface for all LLM calls with agent-specific models
Uses Responses API for reasoning models for better latency control
"""
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from typing import List, Dict, Union, Iterator
import sys
from pathlib import Path
import openai
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger
import config

logger = get_logger(__name__)

class LLMWrapper:
    def __init__(self):
        logger.info("Initializing LLM Wrapper")
        
        # Initialize OpenAI client for Responses API
        self.openai_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        
        # Fallback LLM
        self.fallback_llm = ChatGoogleGenerativeAI(
            model=config.FALLBACK_LLM_MODEL,
            google_api_key=config.GOOGLE_API_KEY
        )
        logger.info(f"Fallback LLM initialized: {config.FALLBACK_LLM_MODEL}")
    
    def _is_gpt5_series(self, model_name: str) -> bool:
        """
        Check if model is GPT-5 series (gpt-5, gpt-5-mini, etc.)
        These models use the Responses API with reasoning_effort
        """
        model_lower = model_name.lower()
        return model_lower.startswith("gpt-5")
    
    def _is_reasoning_model(self, model_name: str) -> bool:
        """
        Check if model supports reasoning_effort parameter
        Includes GPT-5 series, o1, o3, o4
        """
        model_lower = model_name.lower()
        
        # GPT-5 series (including gpt-5-mini)
        if self._is_gpt5_series(model_name):
            return True
        
        # Other reasoning models (o1, o3, o4)
        reasoning_models = ["o1-preview", "o1-mini", "o1", "o3-mini", "o4-mini", "o4", "o3"]
        
        for rm in reasoning_models:
            if model_lower == rm or model_lower.startswith(f"{rm}-"):
                return True
        
        return False
    
    def invoke(
        self,
        model_name: str,
        messages: List[Dict],
        max_tokens: int = None,
        timeout: int = 30,
        reasoning_effort: str = None,
        stream: bool = False
    ) -> Union[str, Iterator[str]]:
        """
        Invoke LLM with automatic fallback
        
        Args:
            model_name: Model to use (e.g., "gpt-5", "gpt-4.1-mini", "sonar-pro")
            messages: List of {"role": "system/user/assistant", "content": "..."}
            max_tokens: Max completion tokens
            timeout: Request timeout in seconds
            reasoning_effort: For reasoning models ("low"/"medium"/"high")
            stream: Stream response tokens
            
        Returns:
            Response content string or stream iterator
        """
        max_tokens = max_tokens or config.MAX_COMPLETION_TOKENS
        
        logger.info(f"Invoking {model_name} (max_tokens={max_tokens}, timeout={timeout}s)")
        
        # Check if it's a GPT-5 series or reasoning model (uses Responses API)
        if self._is_reasoning_model(model_name):
            effort = reasoning_effort or "medium"
            logger.info(f"Using Responses API with reasoning_effort: {effort}")
            
            try:
                # Prepare messages - Responses API supports system messages
                api_messages = messages
                
                start_time = time.time()
                response = self.openai_client.chat.completions.create(
                    model=model_name,
                    messages=api_messages,
                    reasoning_effort=effort,
                    max_completion_tokens=max_tokens,
                    stream=stream,
                    timeout=timeout
                )
                
                if stream:
                    logger.info(f"Streaming from {model_name}")
                    return response
                else:
                    content = response.choices[0].message.content
                    elapsed = time.time() - start_time
                    
                    # Log reasoning tokens if available
                    if hasattr(response, 'usage') and hasattr(response.usage, 'completion_tokens_details'):
                        details = response.usage.completion_tokens_details
                        if hasattr(details, 'reasoning_tokens'):
                            logger.info(f"Reasoning tokens: {details.reasoning_tokens}")
                    
                    logger.info(f"{model_name} responded in {elapsed:.2f}s")
                    return content
                    
            except Exception as e:
                logger.warning(f"{model_name} failed: {str(e)}, falling back to {config.FALLBACK_LLM_MODEL}")
                # Fall through to fallback
        else:
            # Standard OpenAI models (gpt-4.1-mini, gpt-4o, gpt-4-turbo, etc.)
            logger.info(f"Using standard Chat Completions API")
            
            try:
                start_time = time.time()
                response = self.openai_client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    timeout=timeout,
                    stream=stream
                )
                
                if stream:
                    logger.info(f"Streaming from {model_name}")
                    return response
                else:
                    content = response.choices[0].message.content
                    elapsed = time.time() - start_time
                    logger.info(f"{model_name} responded in {elapsed:.2f}s")
                    return content
                    
            except Exception as e:
                logger.warning(f"{model_name} failed: {str(e)}, falling back to {config.FALLBACK_LLM_MODEL}")
                # Fall through to fallback
        
        # Fallback to Gemini
        try:
            logger.info(f"Using fallback: {config.FALLBACK_LLM_MODEL}")
            lc_messages = self._convert_messages(messages)
            
            start_time = time.time()
            if stream:
                return self.fallback_llm.stream(lc_messages)
            else:
                response = self.fallback_llm.invoke(lc_messages)
                elapsed = time.time() - start_time
                logger.info(f"Fallback responded in {elapsed:.2f}s")
                return response.content
                
        except Exception as e2:
            logger.error(f"Fallback also failed: {str(e2)}")
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


def invoke_llm(
    model_name: str,
    messages: List[Dict],
    max_tokens: int = None,
    timeout: int = 30,
    reasoning_effort: str = None,
    stream: bool = False
) -> Union[str, Iterator[str]]:
    """
    Convenience function for LLM calls
    
    Args:
        model_name: Model to use (e.g., "gpt-5", "gpt-4.1-mini")
        messages: List of message dicts
        max_tokens: Max completion tokens
        timeout: Request timeout
        reasoning_effort: For reasoning models ("low"/"medium"/"high")
        stream: Stream response
        
    Returns:
        Response content string or stream iterator
    """
    return llm.invoke(model_name, messages, max_tokens, timeout, reasoning_effort, stream)


# Test
if __name__ == "__main__":
    logger.info("Testing LLM Wrapper")
    test_messages = [
        {"role": "system", "content": "You are a helpful financial advisor."},
        {"role": "user", "content": "What is XIRR?"}
    ]
    
    # Test with gpt-4.1-mini
    response = invoke_llm("gpt-4.1-mini", test_messages, max_tokens=500, timeout=30)
    logger.info(f"Test response received: {len(response)} characters")

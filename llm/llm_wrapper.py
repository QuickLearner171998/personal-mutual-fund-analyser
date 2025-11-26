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
    
    def _is_reasoning_model(self, model_name: str) -> bool:
        """
        Check if model supports reasoning_effort parameter
        """
        model_lower = model_name.lower()
        
        # Exact matches for reasoning models
        reasoning_models = [
            "gpt-5",
            "o1-preview",
            "o1-mini",
            "o1",
            "o3",
            "o4"
        ]
        
        # Check for exact match or model that starts with these patterns
        for rm in reasoning_models:
            # Exact match
            if model_lower == rm:
                return True
            # Pattern match but exclude "mini" and similar variants
            if model_lower.startswith(rm) and "mini" not in model_lower and "nano" not in model_lower:
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
        
        # Check if it's a reasoning model (GPT-5, o1, etc.)
        if self._is_reasoning_model(model_name):
            effort = reasoning_effort or "medium"
            logger.info(f"Using reasoning model with effort: {effort}")
            
            try:
                # Use OpenAI Responses API for reasoning models
                api_messages = []
                for msg in messages:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    
                    if role == "system":
                        # System messages converted to user messages for Responses API
                        api_messages.append({"role": "user", "content": f"System: {content}"})
                    else:
                        api_messages.append({"role": role, "content": content})
                
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
                    logger.info(f"{model_name} responded in {elapsed:.2f}s")
                    return content
                    
            except Exception as e:
                logger.warning(f"{model_name} failed: {str(e)}, falling back to {config.FALLBACK_LLM_MODEL}")
                # Fall through to fallback
        else:
            # Standard OpenAI models (gpt-4.1-mini, gpt-4o, gpt-5-mini, etc.)
            logger.info(f"Using standard model: {model_name}")
            
            try:
                start_time = time.time()
                
                # Check if this is a gpt-5-mini or reasoning-type model that needs max_completion_tokens
                uses_completion_tokens = "gpt-5" in model_name.lower() or "o1" in model_name.lower()
                
                api_params = {
                    "model": model_name,
                    "messages": messages,
                    "timeout": timeout,
                    "stream": stream
                }
                
                # Use correct token parameter based on model
                if uses_completion_tokens:
                    api_params["max_completion_tokens"] = max_tokens
                else:
                    api_params["max_tokens"] = max_tokens
                
                response = self.openai_client.chat.completions.create(**api_params)
                
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

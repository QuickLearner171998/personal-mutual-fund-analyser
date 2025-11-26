"""
Simplified LLM Wrapper for Agent-Specific Models
Clean interface without legacy baggage
"""
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from typing import List, Dict, Union, Iterator
import sys
from pathlib import Path
import openai

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger
import config

logger = get_logger(__name__)

class SimpleLLMWrapper:
    """Simplified LLM wrapper for agent-specific models"""
    
    def __init__(self):
        logger.info("Initializing Simplified LLM Wrapper")
        
        # OpenAI client for Responses API (reasoning models)
        self.openai_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        
        # Fallback LLM
        self.fallback_llm = ChatGoogleGenerativeAI(
            model=config.FALLBACK_LLM_MODEL,
            google_api_key=config.GOOGLE_API_KEY
        )
        logger.info(f"Fallback LLM: {config.FALLBACK_LLM_MODEL}")
    
    def invoke(
        self,
        model_name: str,
        messages: List[Dict],
        max_tokens: int = None,
        timeout: int = None,
        reasoning_effort: str = None,
        stream: bool = False
    ) -> Union[str, Iterator]:
        """
        Invoke LLM with specified model
        
        Args:
            model_name: Model to use
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Max completion tokens
            timeout: Request timeout in seconds
            reasoning_effort: For reasoning models only
            stream: Whether to stream response
        
        Returns:
            Response string or iterator if streaming
        """
        logger.info(f"Invoking model: {model_name}")
        
        # Check if it's a reasoning model
        if self._is_reasoning_model(model_name) and reasoning_effort:
            return self._call_responses_api(
                model_name, messages, max_tokens, reasoning_effort, stream
            )
        
        # Standard OpenAI model
        if model_name.startswith("gpt") or model_name.startswith("o1"):
            return self._call_openai(
                model_name, messages, max_tokens, timeout, stream
            )
        
        # Perplexity models (handled by agents directly)
        if model_name.startswith("sonar"):
            raise ValueError(f"Perplexity model {model_name} should be called directly by agent")
        
        # Unknown model - try OpenAI
        logger.warning(f"Unknown model {model_name}, attempting OpenAI API")
        return self._call_openai(model_name, messages, max_tokens, timeout, stream)
    
    def _is_reasoning_model(self, model_name: str) -> bool:
        """Check if model supports reasoning_effort parameter"""
        model_lower = model_name.lower()
        reasoning_models = ["gpt-5", "o1-preview", "o1-mini", "o1", "o3", "o4"]
        
        for rm in reasoning_models:
            if model_lower == rm or (
                model_lower.startswith(rm) and 
                "mini" not in model_lower and 
                "nano" not in model_lower
            ):
                return True
        return False
    
    def _call_openai(
        self, 
        model: str, 
        messages: List[Dict], 
        max_tokens: int = None,
        timeout: int = None, 
        stream: bool = False
    ) -> Union[str, Iterator]:
        """Call standard OpenAI API"""
        try:
            llm = ChatOpenAI(
                model=model,
                api_key=config.OPENAI_API_KEY,
                max_tokens=max_tokens or 5000,
                timeout=timeout or 120
            )
            
            lc_messages = self._convert_messages(messages)
            
            if stream:
                logger.info(f"Streaming from {model}")
                return llm.stream(lc_messages)
            else:
                logger.info(f"Invoking {model}")
                response = llm.invoke(lc_messages)
                logger.info(f"Received response from {model}")
                return response.content
                
        except Exception as e:
            logger.error(f"OpenAI call failed for {model}: {str(e)}")
            logger.info("Attempting fallback to Gemini")
            return self._call_fallback(messages, stream)
    
    def _call_responses_api(
        self,
        model: str,
        messages: List[Dict],
        max_tokens: int = None,
        reasoning_effort: str = "medium",
        stream: bool = False
    ) -> Union[str, Iterator]:
        """Call OpenAI Responses API for reasoning models"""
        logger.info(f"Using Responses API for {model} with effort={reasoning_effort}")
        
        try:
            params = {
                "model": model,
                "messages": messages,
                "reasoning_effort": reasoning_effort
            }
            
            if max_tokens:
                params["max_completion_tokens"] = max_tokens
            
            if config.INCLUDE_REASONING:
                params["include"] = ["reasoning"]
            
            if stream:
                response = self.openai_client.chat.completions.create(
                    **params,
                    stream=True
                )
                return response
            else:
                response = self.openai_client.chat.completions.create(**params)
                content = response.choices[0].message.content
                logger.info(f"Received response from {model} via Responses API")
                return content
                
        except Exception as e:
            logger.error(f"Responses API failed for {model}: {str(e)}")
            logger.info("Attempting fallback to Gemini")
            return self._call_fallback(messages, stream)
    
    def _call_fallback(self, messages: List[Dict], stream: bool = False) -> Union[str, Iterator]:
        """Call fallback model (Gemini)"""
        try:
            lc_messages = self._convert_messages(messages)
            if stream:
                return self.fallback_llm.stream(lc_messages)
            else:
                response = self.fallback_llm.invoke(lc_messages)
                logger.info("Successfully received response from fallback")
                return response.content
        except Exception as e:
            logger.error(f"Fallback also failed: {str(e)}")
            raise
    
    def _convert_messages(self, messages: List[Dict]) -> List:
        """Convert dict messages to LangChain format"""
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
_llm_wrapper = None

def get_llm_wrapper():
    """Get global LLM wrapper instance"""
    global _llm_wrapper
    if _llm_wrapper is None:
        _llm_wrapper = SimpleLLMWrapper()
    return _llm_wrapper


def invoke_llm(
    model_name: str,
    messages: List[Dict],
    max_tokens: int = None,
    timeout: int = None,
    reasoning_effort: str = None,
    stream: bool = False
) -> Union[str, Iterator]:
    """
    Convenience function to invoke LLM
    
    Args:
        model_name: Model to use
        messages: List of message dicts
        max_tokens: Max completion tokens
        timeout: Request timeout
        reasoning_effort: For reasoning models
        stream: Whether to stream
    
    Returns:
        Response string or iterator
    """
    wrapper = get_llm_wrapper()
    return wrapper.invoke(
        model_name=model_name,
        messages=messages,
        max_tokens=max_tokens,
        timeout=timeout,
        reasoning_effort=reasoning_effort,
        stream=stream
    )

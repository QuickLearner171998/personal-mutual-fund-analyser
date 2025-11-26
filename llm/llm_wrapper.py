"""
LLM Wrapper with GPT-4o + Gemini Fallback
Unified interface for all LLM calls
Uses Responses API for GPT-5/o1 reasoning models for better latency control
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
        
        # Primary LLM
        self.primary_llm = ChatOpenAI(
            model=config.PRIMARY_LLM_MODEL,
            api_key=config.OPENAI_API_KEY,
            max_tokens=config.MAX_COMPLETION_TOKENS_PRIMARY,
            timeout=config.PRIMARY_TIMEOUT
        )
        logger.info(f"Primary LLM initialized: {config.PRIMARY_LLM_MODEL}")
        
        # RAG LLM
        self.rag_llm = ChatOpenAI(
            model=config.RAG_LLM_MODEL,
            api_key=config.OPENAI_API_KEY,
            max_tokens=config.MAX_COMPLETION_TOKENS_PRIMARY,
            timeout=config.PRIMARY_TIMEOUT
        )
        logger.info(f"RAG LLM initialized: {config.RAG_LLM_MODEL}")
        
        # Intent Classification LLM
        self.intent_llm = ChatOpenAI(
            model=config.INTENT_CLASSIFICATION_MODEL,
            api_key=config.OPENAI_API_KEY,
            max_tokens=1000,  # Intent classification needs short responses
            timeout=10  # Fast timeout for intent
        )
        logger.info(f"Intent Classification LLM initialized: {config.INTENT_CLASSIFICATION_MODEL}")
        
        # Note: Reasoning LLM will use Responses API directly, not LangChain
        logger.info(f"Reasoning LLM will use Responses API: {config.REASONING_LLM_MODEL}")
        logger.info(f"Default reasoning effort: {config.REASONING_EFFORT_DEFAULT}")
        
        # Fallback LLM
        self.fallback_llm = ChatGoogleGenerativeAI(
            model=config.FALLBACK_LLM_MODEL,
            google_api_key=config.GOOGLE_API_KEY
        )
        logger.info(f"Fallback LLM initialized: {config.FALLBACK_LLM_MODEL}")
    
    def _is_reasoning_model(self, model_name: str) -> bool:
        """
        Check if model supports reasoning_effort parameter (GPT-5/o1 series)
        Note: gpt-5-mini, gpt-4.1-mini, etc. are NOT reasoning models
        """
        model_lower = model_name.lower()
        
        # Exact matches for reasoning models
        reasoning_models = [
            "gpt-5",           # Full GPT-5
            "o1-preview",      # O1 preview
            "o1-mini",         # O1 mini
            "o1",              # O1 base
            "o3",              # O3 series
            "o4"               # O4 series
        ]
        
        # Check for exact match or model that starts with these patterns
        for rm in reasoning_models:
            # Exact match
            if model_lower == rm:
                return True
            # Pattern match but exclude "mini" and similar variants
            if model_lower.startswith(rm) and "mini" not in model_lower and "nano" not in model_lower:
                # e.g., "gpt-5-turbo" would match, but "gpt-5-mini" won't
                return True
        
        return False
    
    def _call_reasoning_api(self, messages: List[Dict], reasoning_effort: str = None, stream: bool = False) -> Union[str, Iterator]:
        """
        Call OpenAI Responses API for reasoning models (GPT-5/o1)
        This API is optimized for reasoning models with better latency control
        
        Args:
            messages: List of message dicts
            reasoning_effort: "low", "medium", or "high"
            stream: Whether to stream response
            
        Returns:
            Response content or stream iterator
        """
        effort = reasoning_effort or config.REASONING_EFFORT_DEFAULT
        
        logger.info(f"Using Responses API for {config.REASONING_LLM_MODEL}")
        logger.info(f"Reasoning effort: {effort}, Max tokens: {config.MAX_COMPLETION_TOKENS_REASONING}")
        
        start_time = time.time()
        
        try:
            # Prepare messages for Responses API
            api_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                # Responses API format
                if role == "system":
                    # System messages are handled differently in Responses API
                    api_messages.append({"role": "user", "content": f"System: {content}"})
                else:
                    api_messages.append({"role": role, "content": content})
            
            # Call Responses API with reasoning parameters
            response = self.openai_client.chat.completions.create(
                model=config.REASONING_LLM_MODEL,
                messages=api_messages,
                reasoning_effort=effort,
                max_completion_tokens=config.MAX_COMPLETION_TOKENS_REASONING,
                stream=stream,
                timeout=config.REASONING_TIMEOUT,
                # Additional optimizations
                store=config.ENABLE_PROMPT_CACHING  # Enable prompt caching if supported
            )
            
            elapsed = time.time() - start_time
            
            if stream:
                logger.info(f"Started streaming from Reasoning API (effort: {effort})")
                return response
            else:
                content = response.choices[0].message.content
                
                # Log reasoning token usage if available
                if hasattr(response, 'usage'):
                    usage = response.usage
                    logger.info(f"Reasoning API tokens - Prompt: {usage.prompt_tokens}, "
                              f"Completion: {usage.completion_tokens}, "
                              f"Total: {usage.total_tokens}")
                
                logger.info(f"Reasoning API response received in {elapsed:.2f}s (effort: {effort})")
                return content
                
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Reasoning API failed after {elapsed:.2f}s: {str(e)}")
            raise
    
    def invoke(self, messages: List[Dict], use_reasoning: bool = False, use_rag: bool = False, use_intent: bool = False, reasoning_effort: str = None, stream: bool = False):
        """
        Invoke LLM with automatic fallback
        Uses Responses API for reasoning models (GPT-5/o1) for better latency control
        
        Args:
            messages: List of {"role": "system/user/assistant", "content": "..."}
            use_reasoning: Use reasoning model for advanced thinking
            use_rag: Use fast model for simple RAG queries
            use_intent: Use dedicated intent classification model
            reasoning_effort: Override default reasoning effort ("low"/"medium"/"high" - only for GPT-5/o1)
            stream: Stream response tokens
        """
        # Choose model
        if use_intent:
            model_name = "Intent Classification"
            current_model = config.INTENT_CLASSIFICATION_MODEL
            logger.info(f"Using {model_name} LLM: {current_model}")
            
            # Convert to LangChain format
            lc_messages = self._convert_messages(messages)
            
            try:
                if stream:
                    logger.info(f"Streaming response from {model_name} LLM")
                    return self.intent_llm.stream(lc_messages)
                else:
                    logger.info(f"Invoking {model_name} LLM")
                    response = self.intent_llm.invoke(lc_messages)
                    logger.info(f"Successfully received response from {model_name} LLM")
                    return response.content
            except Exception as e:
                logger.error(f"{model_name} LLM failed: {str(e)}")
                raise
                
        elif use_reasoning:
            # Use Responses API for reasoning models
            model_name = "Reasoning"
            current_model = config.REASONING_LLM_MODEL
            logger.info(f"Using {model_name} LLM: {current_model}")
            
            if self._is_reasoning_model(current_model):
                try:
                    return self._call_reasoning_api(messages, reasoning_effort, stream)
                except Exception as e:
                    logger.warning(f"{model_name} LLM failed: {str(e)}, falling back to {config.FALLBACK_LLM_MODEL}")
                    # Fall through to fallback
            else:
                logger.warning(f"{current_model} is not a reasoning model, using standard API")
                # Fall through to standard LangChain call
                
        elif use_rag:
            model_name = "RAG"
            current_model = config.RAG_LLM_MODEL
            llm = self.rag_llm
        else:
            model_name = "Primary"
            current_model = config.PRIMARY_LLM_MODEL
            llm = self.primary_llm
        
        # Standard LangChain invocation for non-reasoning models
        if not use_reasoning or not self._is_reasoning_model(config.REASONING_LLM_MODEL):
            logger.info(f"Using {model_name} LLM: {current_model}")
            lc_messages = self._convert_messages(messages)
            
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
                logger.warning(f"{model_name} LLM failed: {str(e)}, falling back to {config.FALLBACK_LLM_MODEL}")
                # Fall through to fallback
        
        # Fallback to Gemini
        try:
            lc_messages = self._convert_messages(messages)
            if stream:
                logger.info(f"Streaming response from Fallback LLM")
                return self.fallback_llm.stream(lc_messages)
            else:
                logger.info(f"Invoking Fallback LLM")
                response = self.fallback_llm.invoke(lc_messages)
                logger.info(f"Successfully received response from Fallback LLM")
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


def invoke_llm(messages: List[Dict], use_reasoning: bool = False, use_rag: bool = False, use_intent: bool = False, reasoning_effort: str = None, stream: bool = False):
    """
    Convenience function for LLM calls
    
    Args:
        messages: List of message dicts
        use_reasoning: Use reasoning model
        use_rag: Use RAG model
        use_intent: Use intent classification model
        reasoning_effort: Override reasoning effort ("low"/"medium"/"high")
        stream: Stream response
    """
    return llm.invoke(messages, use_reasoning, use_rag, use_intent, reasoning_effort, stream)


# Test
if __name__ == "__main__":
    logger.info("Testing LLM Wrapper")
    test_messages = [
        {"role": "system", "content": "You are a helpful financial advisor."},
        {"role": "user", "content": "What is XIRR?"}
    ]
    
    response = invoke_llm(test_messages)
    logger.info(f"Test response received: {len(response)} characters")

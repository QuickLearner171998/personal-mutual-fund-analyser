"""
LLM Wrapper with GPT-4o + Gemini Fallback
Unified interface for all LLM calls
"""
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from typing import List, Dict, Union, Iterator
import config

class LLMWrapper:
    def __init__(self):
        # Primary: gpt-4o
        self.primary_llm = ChatOpenAI(
            model=config.PRIMARY_LLM_MODEL,
            temperature=config.PRIMARY_LLM_TEMPERATURE,
            max_tokens=config.PRIMARY_LLM_MAX_TOKENS,
            api_key=config.OPENAI_API_KEY
        )
        
        # RAG: gpt-4o-mini (fast for simple queries)
        self.rag_llm = ChatOpenAI(
            model=config.RAG_LLM_MODEL,
            temperature=config.RAG_LLM_TEMPERATURE,
            max_tokens=config.RAG_LLM_MAX_TOKENS,
            api_key=config.OPENAI_API_KEY
        )
        
        # Reasoning: gpt-4o (or o1 if you have access)
        self.reasoning_llm = ChatOpenAI(
            model=config.REASONING_LLM_MODEL,
            temperature=config.REASONING_LLM_TEMPERATURE,
            api_key=config.OPENAI_API_KEY
        )
        
        # Fallback: Gemini
        self.fallback_llm = ChatGoogleGenerativeAI(
            model=config.FALLBACK_LLM_MODEL,
            temperature=config.FALLBACK_LLM_TEMPERATURE,
            max_output_tokens=config.FALLBACK_LLM_MAX_TOKENS,
            google_api_key=config.GOOGLE_API_KEY
        )
    
    def invoke(self, messages: List[Dict], use_reasoning: bool = False, use_rag: bool = False, stream: bool = False):
        """
        Invoke LLM with automatic fallback
        
        Args:
            messages: List of {"role": "system/user/assistant", "content": "..."}
            use_reasoning: Use o1-preview for advanced reasoning
            use_rag: Use fast gpt-4o-mini for simple RAG queries
            stream: Stream response tokens
        """
        # Convert to LangChain format
        lc_messages = self._convert_messages(messages)
        
        # Choose model
        if use_reasoning:
            llm = self.reasoning_llm
        elif use_rag:
            llm = self.rag_llm
        else:
            llm = self.primary_llm
        
        try:
            if stream:
                return llm.stream(lc_messages)
            else:
                response = llm.invoke(lc_messages)
                return response.content
                
        except Exception as e:
            print(f"⚠️ Primary LLM failed: {str(e)}, falling back to Gemini...")
            
            try:
                if stream:
                    return self.fallback_llm.stream(lc_messages)
                else:
                    response = self.fallback_llm.invoke(lc_messages)
                    return response.content
            except Exception as e2:
                print(f"❌ Fallback failed: {str(e2)}")
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


def invoke_llm(messages: List[Dict], use_reasoning: bool = False, use_rag: bool = False, stream: bool = False):
    """Convenience function for LLM calls"""
    return llm.invoke(messages, use_reasoning, use_rag, stream)


# Test
if __name__ == "__main__":
    test_messages = [
        {"role": "system", "content": "You are a helpful financial advisor."},
        {"role": "user", "content": "What is XIRR?"}
    ]
    
    response = invoke_llm(test_messages)
    print(f"Response: {response}")

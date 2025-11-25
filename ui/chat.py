"""
AI Chat Interface - Multi-Agent Q&A
"""
import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from agents.orchestrator import answer_query

def render_chat():
    st.markdown('<div class="main-header">💬 AI Portfolio Q&A</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Example prompts
    with st.expander("💡 Example Questions"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
**Portfolio Analysis:**
- What is my total portfolio value?
- Show my top 5 holdings
- What's my equity vs debt allocation?
- Which fund has the best returns?

**Goal Planning:**
- How much SIP for ₹1 crore in 15 years?
- Am I on track for my retirement goal?
- What's my portfolio projected value in 10 years?
            """)
        with col2:
            st.markdown("""
**Market Research:**
- Latest NAV of HDFC Flexi Cap Fund?
- Recent news on SBI Small Cap Fund?
- How is the mutual fund market performing?

**Strategy Advice:**
- Should I rebalance my portfolio?
- Am I taking too much risk?
- Tax optimization opportunities?
- Where should I invest more?
            """)
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your portfolio..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response with streaming
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            try:
                # Try streaming first
                response_stream = answer_query(prompt, stream=True)
                
                # Check if it's actually a stream or just a string
                if isinstance(response_stream, str):
                    # Not streaming, just display
                    message_placeholder.markdown(response_stream)
                    full_response = response_stream
                else:
                    # Streaming - display token by token
                    full_response = ""
                    for chunk in response_stream:
                        if hasattr(chunk, 'content'):
                            full_response += chunk.content
                        else:
                            full_response += str(chunk)
                        message_placeholder.markdown(full_response + "▌")
                    
                    message_placeholder.markdown(full_response)
                
                # Add to history
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                error_msg = f"⚠️ Error: {str(e)}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

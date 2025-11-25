"""
Settings page
"""
import streamlit as st

def render_settings():
    st.markdown('<div class="main-header">⚙️ Settings</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    st.subheader("Database")
    st.text_input("MongoDB URI", type="password", disabled=True, value="Connected")
    
    st.markdown("---")
    
    st.subheader("LLM Configuration")
    st.selectbox("Primary LLM", ["GPT-4 Turbo", "Gemini 2.0 Flash"], disabled=True)
    st.selectbox("Fallback LLM", ["Gemini 2.0 Flash", "GPT-4 Turbo"], disabled=True)
    
    st.markdown("---")
    
    st.subheader("Data Management")
    if st.button("🗑️ Clear Portfolio Data"):
        st.warning("This will delete all your portfolio data. This action cannot be undone.")
    
    st.markdown("---")
    st.caption("Version 1.0.0")

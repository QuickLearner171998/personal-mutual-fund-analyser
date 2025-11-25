"""
Main Streamlit Application for MF Portfolio Bot
"""
import streamlit as st
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Page config
st.set_page_config(
    page_title="MF Portfolio Bot",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .positive {
        color: #10b981;
    }
    .negative {
        color: #ef4444;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    st.title("💹 MF Portfolio")
    st.markdown("---")
    
    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "💰 SIP Analysis", "💬 AI Q&A", "📁 Upload CAS", "⚙️ Settings"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.caption("Built with ❤️ using Streamlit")

# Main content
if page == "📊 Dashboard":
    from ui.dashboard import render_dashboard
    render_dashboard()

elif page == "💰 SIP Analysis":
    from ui.sip_dashboard import render_sip_dashboard
    render_sip_dashboard()


    
elif page == "💬 AI Q&A":
    from ui.chat import render_chat
    render_chat()
    
elif page == "📁 Upload CAS":
    from ui.cas_upload import render_cas_upload
    render_cas_upload()
    
elif page == "⚙️ Settings":
    from ui.settings import render_settings
    render_settings()

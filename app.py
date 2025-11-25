"""
Main Streamlit Application for MF Portfolio Analyzer
Enhanced for MF Central data sources
"""
import streamlit as st
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Page config
st.set_page_config(
    page_title="MF Portfolio Analyzer",
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
    .stDataFrame {
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    st.title("💹 MF Portfolio")
    st.markdown("---")
    
    page = st.radio(
        "Navigation",
        [
            "📊 Dashboard", 
            "💰 SIP Analytics", 
            "💬 AI Q&A", 
            "📁 Upload MF Central Data"
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Quick stats in sidebar
    try:
        from database.json_store import PortfolioStore
        store = PortfolioStore()
        portfolio = store.get_portfolio()
        
        if portfolio:
            st.markdown("### Quick Stats")
            st.metric("Total Value", f"₹{portfolio.get('total_value', 0):,.0f}")
            st.metric("Total Gain", f"₹{portfolio.get('total_gain', 0):,.0f}")
            st.metric("XIRR", f"{portfolio.get('xirr', 0):.2f}%")
            st.metric("Active SIPs", portfolio.get('num_active_sips', 0))
    except:
        pass
    
    st.markdown("---")
    st.caption("Built with ❤️ using Streamlit")
    st.caption("Data source: MF Central")

# Main content
if page == "📊 Dashboard":
    from ui.dashboard import render_dashboard
    render_dashboard()

elif page == "💰 SIP Analytics":
    from ui.sip_analytics import render_sip_dashboard
    render_sip_dashboard()

elif page == "💬 AI Q&A":
    from ui.chat import render_chat
    render_chat()
    
elif page == "📁 Upload MF Central Data":
    from ui.cas_upload import render_upload_page
    render_upload_page()

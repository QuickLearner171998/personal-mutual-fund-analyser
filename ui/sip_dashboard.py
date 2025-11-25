"""
SIP Analysis Dashboard
"""
import streamlit as st
import pandas as pd
from database.json_store import PortfolioStore

def render_sip_dashboard():
    st.markdown('<div class="main-header">💰 SIP Analysis</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    store = PortfolioStore()
    transactions = store.get_transactions()
    
    if not transactions:
        st.info("No transaction data found. Upload your CAS to see SIP analysis.")
        return
    
    # Filter SIP transactions
    sip_txns = [t for t in transactions if 'systematic' in t.get('description', '').lower() or 'sip' in t.get('description', '').lower()]
    
    st.metric("Total SIP Transactions", len(sip_txns))
    
    if sip_txns:
        # Convert to DataFrame
        df = pd.DataFrame(sip_txns)
        
        # Monthly SIP amount estimate
        if 'amount' in df.columns:
            avg_sip = df['amount'].median()
            total_sip_invested = df['amount'].sum()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Average SIP Amount", f"₹{avg_sip:,.0f}")
            with col2:
                st.metric("Total SIP Invested", f"₹{total_sip_invested:,.0f}")
        
        # SIP Timeline
        st.subheader("📅 SIP Transaction History")
        display_df = df[['date', 'description', 'amount', 'units']].copy()
        display_df.columns = ['Date', 'Description', 'Amount', 'Units']
        display_df['Amount'] = display_df['Amount'].apply(lambda x: f"₹{x:,.2f}")
        display_df['Units'] = display_df['Units'].apply(lambda x: f"{x:.3f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.warning("No SIP transactions found in your portfolio.")

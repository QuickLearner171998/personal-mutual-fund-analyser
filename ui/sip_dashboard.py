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
    
    if not sip_txns:
        st.warning("No SIP transactions found in your portfolio.")
        return

    # Identify Active SIPs (last txn within 45 days)
    from datetime import datetime, timedelta
    
    active_sips = []
    inactive_sips = []
    
    # Group by scheme
    sip_by_scheme = {}
    for txn in sip_txns:
        scheme = txn['scheme_name']
        if scheme not in sip_by_scheme:
            sip_by_scheme[scheme] = []
        sip_by_scheme[scheme].append(txn)
    
    today = datetime.now().date()
    cutoff_date = today - timedelta(days=45)
    
    for scheme, txns in sip_by_scheme.items():
        # Sort by date
        txns.sort(key=lambda x: datetime.strptime(x['date'], '%d-%b-%Y').date() if isinstance(x['date'], str) else x['date'], reverse=True)
        last_txn = txns[0]
        last_date = last_txn['date']
        if isinstance(last_date, str):
            last_date = datetime.strptime(last_date, '%d-%b-%Y').date()
            
        is_active = last_date >= cutoff_date
        
        sip_info = {
            'scheme_name': scheme,
            'amount': last_txn['amount'],
            'last_date': last_date,
            'total_invested': sum(t['amount'] for t in txns),
            'txn_count': len(txns)
        }
        
        if is_active:
            active_sips.append(sip_info)
        else:
            inactive_sips.append(sip_info)
            
    st.metric("Active SIPs", len(active_sips))
    
    if active_sips:
        st.subheader("✅ Active SIPs")
        active_df = pd.DataFrame(active_sips)
        
        display_df = active_df[['scheme_name', 'amount', 'last_date', 'total_invested']].copy()
        display_df.columns = ['Fund Name', 'SIP Amount', 'Last Date', 'Total Invested via SIP']
        display_df['SIP Amount'] = display_df['SIP Amount'].apply(lambda x: f"₹{x:,.0f}")
        display_df['Total Invested via SIP'] = display_df['Total Invested via SIP'].apply(lambda x: f"₹{x:,.0f}")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No active SIPs found (last 45 days).")

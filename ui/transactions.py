"""
Transaction History View
"""
import streamlit as st
import pandas as pd
from database.json_store import PortfolioStore
from datetime import datetime, timedelta

def render_transactions():
    st.markdown('<div class="main-header">📝 Transaction History</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    store = PortfolioStore()
    transactions = store.get_transactions()
    
    if not transactions:
        st.info("No transactions found. Upload your CAS to see transaction history.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(transactions)
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        txn_types = ['All'] + list(df['type'].unique()) if 'type' in df.columns else ['All']
        selected_type = st.selectbox("Transaction Type", txn_types)
    
    with col2:
        date_range = st.selectbox("Date Range", ["All Time", "Last Month", "Last 3 Months", "Last Year"])
    
    with col3:
        if 'scheme_name' in df.columns:
            funds = ['All'] + sorted(df['scheme_name'].unique().tolist())
            selected_fund = st.selectbox("Fund", funds, key='fund_filter')
        else:
            selected_fund = 'All'
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_type != 'All':
        filtered_df = filtered_df[filtered_df['type'] == selected_type]
    
    if selected_fund != 'All':
        filtered_df = filtered_df[filtered_df['scheme_name'] == selected_fund]
    
    if date_range != "All Time" and 'date' in df.columns:
        end_date = datetime.now()
        if date_range == "Last Month":
            start_date = end_date - timedelta(days=30)
        elif date_range == "Last 3 Months":
            start_date = end_date - timedelta(days=90)
        else:  # Last Year
            start_date = end_date - timedelta(days=365)
        
        filtered_df['date_obj'] = pd.to_datetime(filtered_df['date'])
        filtered_df = filtered_df[filtered_df['date_obj'] >= start_date]
    
    # Display summary
    st.metric("Total Transactions", len(filtered_df))
    
    # Display table
    if not filtered_df.empty:
        display_cols = ['date', 'description', 'type', 'amount', 'units', 'nav']
        available_cols = [col for col in display_cols if col in filtered_df.columns]
        
        display_df = filtered_df[available_cols].copy()
        display_df.columns = [col.title() for col in available_cols]
        
        if 'Amount' in display_df.columns:
            display_df['Amount'] = display_df['Amount'].apply(lambda x: f"₹{x:,.2f}")
        if 'Units' in display_df.columns:
            display_df['Units'] = display_df['Units'].apply(lambda x: f"{x:.3f}")
        if 'Nav' in display_df.columns:
            display_df['Nav'] = display_df['Nav'].apply(lambda x: f"₹{x:.2f}")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)
        
        # Export button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Export to CSV",
            data=csv,
            file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.warning("No transactions match the selected filters.")

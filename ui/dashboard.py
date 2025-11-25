"""
Enhanced Dashboard with Historical Data, Charts, and Analytics
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from database.json_store import PortfolioStore
from utils.history_tracker import tracker
from datetime import date, timedelta

from utils.formatters import format_currency

def render_dashboard():
    st.markdown('<div class="main-header">📊 Portfolio Dashboard</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Load portfolio with error handling
    try:
        store = PortfolioStore()
        portfolio = store.get_portfolio()
    except Exception as e:
        st.error(f"❌ Error loading portfolio: {str(e)}")
        st.info("Please try uploading your CAS PDF again.")
        return
    
    if not portfolio or not portfolio.get('holdings'):
        st.info("👋 Welcome! Please upload your CAS PDF to get started.")
        st.markdown("""
        ### Getting Started:
        1. Go to **📁 Upload CAS** in the sidebar
        2. Upload your Consolidated Account Statement (CAS) PDF
        3. Your portfolio will be automatically analyzed
        """)
        return
    
    # Top Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    total_value = portfolio.get('total_value', 0)
    total_invested = portfolio.get('total_invested', 0)
    total_gain = portfolio.get('total_gain', 0)
    xirr = portfolio.get('xirr', 0)
    gain_pct = (total_gain / total_invested * 100) if total_invested > 0 else 0
    
    with col1:
        st.metric("Total Current Value", format_currency(total_value))
    with col2:
        st.metric("Total Invested", format_currency(total_invested))
    with col3:
        st.metric("Total Gain/Loss", format_currency(total_gain), delta=f"{gain_pct:.2f}%")
    with col4:
        st.metric("Portfolio XIRR", f"{xirr:.2f}%" if xirr else "N/A")
    
    st.markdown("---")
    
    # Period Returns
    st.subheader("📈 Period Returns")
    ret_col1, ret_col2, ret_col3, ret_col4, ret_col5 = st.columns(5)
    
    periods = [
        (30, "1 Month", ret_col1),
        (90, "3 Months", ret_col2),
        (180, "6 Months", ret_col3),
        (365, "1 Year", ret_col4),
        (1095, "3 Years", ret_col5)
    ]
    
    for days, label, col in periods:
        with col:
            ret = tracker.calculate_period_return(days)
            if ret is not None:
                st.metric(label, f"{ret:+.2f}%")
            else:
                st.metric(label, "N/A")
    
    st.markdown("---")
    
    # Portfolio Timeline Chart
    st.subheader("💹 Portfolio Value Timeline")
    timeline_data = tracker.get_timeline_data(days=365)
    
    if timeline_data:
        df_timeline = pd.DataFrame(timeline_data)
        fig_timeline = go.Figure()
        fig_timeline.add_trace(go.Scatter(
            x=df_timeline['date'],
            y=df_timeline['total_value'],
            mode='lines+markers',
            name='Portfolio Value',
            line=dict(color='#1f77b4', width=2)
        ))
        fig_timeline.update_layout(
            xaxis_title="Date",
            yaxis_title="Value (₹)",
            hovermode='x unified',
            height=300
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info("📊 Timeline data will appear as you track your portfolio over time")
    
    st.markdown("---")
    
    # Two columns: Holdings Table + Charts
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("💼 Holdings")
        holdings_df = pd.DataFrame(portfolio.get('holdings', []))
        
        if not holdings_df.empty:
            # Add gain/loss calculation
            holdings_df['gain_loss'] = holdings_df['current_value'] - holdings_df.get('invested_value', 0)
            holdings_df['gain_loss_pct'] = (holdings_df['gain_loss'] / holdings_df.get('invested_value', 1)) * 100
            
            display_df = holdings_df[[
                'scheme_name', 'current_value', 'gain_loss', 'gain_loss_pct'
            ]].copy()
            display_df.columns = ['Fund Name', 'Current Value', 'Gain/Loss', 'Return %']
            display_df['Current Value'] = display_df['Current Value'].apply(format_currency)
            display_df['Gain/Loss'] = display_df['Gain/Loss'].apply(format_currency)
            display_df['Return %'] = display_df['Return %'].apply(lambda x: f"{x:.2f}%")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)
    
    with col_right:
        st.subheader("📊 Asset Allocation")
        allocation = portfolio.get('allocation', {})
        
        if allocation:
            labels = ['Equity', 'Debt', 'Hybrid', 'Other']
            values = [
                allocation.get('equity', 0),
                allocation.get('debt', 0),
                allocation.get('hybrid', 0),
                allocation.get('other', 0)
            ]
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker=dict(colors=['#10b981', '#3b82f6', '#f59e0b', '#6b7280'])
            )])
            fig_pie.update_layout(height=300, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)
    
    st.markdown("---")
    
    # Top Gainers and Losers
    st.subheader("🏆 Top Performers")
    
    if not holdings_df.empty:
        sorted_by_gain = holdings_df.sort_values('gain_loss_pct', ascending=False)
        
        col_gain, col_loss = st.columns(2)
        
        with col_gain:
            st.markdown("**✅ Top 5 Gainers**")
            top_5 = sorted_by_gain.head(5)[['scheme_name', 'gain_loss_pct', 'current_value']]
            for idx, row in top_5.iterrows():
                st.success(f"**{row['scheme_name'][:40]}**  \n+{row['gain_loss_pct']:.2f}% • {format_currency(row['current_value'])}")
        
        with col_loss:
            st.markdown("**❌ Top 5 Losers**")
            bottom_5 = sorted_by_gain.tail(5)[['scheme_name', 'gain_loss_pct', 'current_value']]
            for idx, row in bottom_5.iterrows():
                st.error(f"**{row['scheme_name'][:40]}**  \n{row['gain_loss_pct']:.2f}% • {format_currency(row['current_value'])}")
    
    st.markdown("---")
    
    # Fund-wise CAGR Chart
    st.subheader("📊 Fund-wise Performance (CAGR)")
    
    if not holdings_df.empty and 'gain_loss_pct' in holdings_df.columns:
        # Use gain % as proxy for CAGR (simplified)
        top_10_cagr = holdings_df.nlargest(10, 'gain_loss_pct')[['scheme_name', 'gain_loss_pct']]
        
        fig_cagr = go.Figure(go.Bar(
            x=top_10_cagr['gain_loss_pct'],
            y=top_10_cagr['scheme_name'].apply(lambda x: x[:30]),
            orientation='h',
            marker=dict(color=top_10_cagr['gain_loss_pct'], colorscale='RdYlGn')
        ))
        fig_cagr.update_layout(
            xaxis_title="Return %",
            yaxis_title="",
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig_cagr, use_container_width=True)
    
    st.markdown("---")
    
    # Category Performance
    st.subheader("📂 Category-wise Performance")
    
    if not holdings_df.empty:
        category_summary = holdings_df.groupby('type').agg({
            'current_value': 'sum',
            'gain_loss': 'sum'
        }).reset_index()
        category_summary['return_pct'] = (category_summary['gain_loss'] / category_summary['current_value']) * 100
        category_summary.columns = ['Category', 'Current Value', 'Gain/Loss', 'Return %']
        category_summary['Current Value'] = category_summary['Current Value'].apply(format_currency)
        category_summary['Gain/Loss'] = category_summary['Gain/Loss'].apply(format_currency)
        category_summary['Return %'] = category_summary['Return %'].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(category_summary, use_container_width=True, hide_index=True)
    
    st.caption(f"Last updated: {portfolio.get('last_updated', 'Never')}")

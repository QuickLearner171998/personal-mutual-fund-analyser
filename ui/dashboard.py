"""
Enhanced Dashboard with MF Central Data
Comprehensive portfolio analytics with XIRR, CAGR, SIPs, and Broker analysis
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from database.json_store import PortfolioStore
from utils.formatters import format_currency
from datetime import date, timedelta


def render_dashboard():
    st.markdown('<div class="main-header">📊 Portfolio Dashboard</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Load portfolio data
    try:
        store = PortfolioStore()
        data = store.get_complete_data()
        portfolio = data.get('portfolio')
        transactions = data.get('transactions', [])
        sips = data.get('sips', [])
        brokers = data.get('brokers', {})
    except Exception as e:
        st.error(f"❌ Error loading portfolio: {str(e)}")
        return
    
    if not portfolio or not portfolio.get('holdings'):
        st.info("👋 Welcome! Please upload your MF Central files to get started.")
        st.markdown("""
        ### Getting Started:
        1. Go to **📁 Upload MF Central Data** in the sidebar
        2. Upload your 3 JSON files from MF Central
        3. Your portfolio will be automatically analyzed
        """)
        return
    
    # View toggle: Aggregated vs Individual
    view_mode = st.radio(
        "View Mode:",
        ["Aggregated Funds", "Individual Folios"],
        horizontal=True,
        help="Aggregated view merges same funds across different folios"
    )
    
    holdings = portfolio.get('aggregated_holdings', []) if view_mode == "Aggregated Funds" else portfolio.get('holdings', [])
    
    st.markdown("---")
    
    # Top Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Value", format_currency(portfolio.get('total_value', 0)))
    
    with col2:
        st.metric("Total Invested", format_currency(portfolio.get('total_invested', 0)))
    
    with col3:
        gain = portfolio.get('total_gain', 0)
        gain_pct = portfolio.get('total_gain_percent', 0)
        st.metric("Total Gain/Loss", format_currency(gain), delta=f"{gain_pct:.2f}%")
    
    with col4:
        xirr = portfolio.get('xirr', 0)
        st.metric("Portfolio XIRR", f"{xirr:.2f}%" if xirr else "N/A")
    
    with col5:
        st.metric("Active SIPs", portfolio.get('num_active_sips', 0))
    
    st.markdown("---")
    
    # Holdings Table with Enhanced Columns
    st.subheader("💼 Holdings")
    
    # Add aggregation toggle
    if view_mode == "Aggregated Funds" and portfolio.get('aggregation_map'):
        st.caption(f"ℹ️ {len(portfolio.get('aggregation_map', {}))} funds aggregated across multiple folios")
    
    holdings_df = pd.DataFrame(holdings)
    
    if not holdings_df.empty:
        # Prepare display dataframe
        # Prepare display columns based on what's available
        base_columns = ['scheme_name', 'amc', 'current_value', 'cost_value', 'gain_loss', 'gain_loss_percent']
        optional_columns = []
        
        # Add optional columns if they exist
        if 'xirr' in holdings_df.columns:
            optional_columns.append('xirr')
        if 'broker' in holdings_df.columns:
            optional_columns.append('broker')
        if 'is_aggregated' in holdings_df.columns:
            optional_columns.append('is_aggregated')
        
        display_columns = base_columns + [col for col in optional_columns if col in holdings_df.columns]
        display_df = holdings_df[display_columns].copy()
        
        # Map internal column names to display names
        column_name_map = {
            'scheme_name': 'Fund Name',
            'amc': 'AMC',
            'current_value': 'Current Value',
            'cost_value': 'Invested',
            'gain_loss': 'Gain/Loss',
            'gain_loss_percent': 'Return %',
            'xirr': 'XIRR %',
            'broker': 'Broker',
            'is_aggregated': 'Aggregated' # Assuming 'is_aggregated' might be displayed
        }
        
        display_df.columns = [column_name_map.get(col, col) for col in display_columns]
        
        # Format columns
        display_df['Current Value'] = display_df['Current Value'].apply(format_currency)
        display_df['Invested'] = display_df['Invested'].apply(format_currency)
        display_df['Gain/Loss'] = display_df['Gain/Loss'].apply(format_currency)
        display_df['Return %'] = display_df['Return %'].apply(lambda x: f"{x:.2f}%")
        
        # Format optional columns if they exist
        if 'XIRR %' in display_df.columns:
            display_df['XIRR %'] = display_df['XIRR %'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) and x != 0 else "-")
        if 'Broker' in display_df.columns:
            display_df['Broker'] = display_df['Broker'].fillna('Unknown')
        
        # Display with sorting
        st.dataframe(
            display_df, 
            use_container_width=True, 
            hide_index=True, 
            height=400
        )
    
    st.markdown("---")
    
    # Charts Row
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        # Top Performers Chart
        st.subheader("🏆 Top 10 Performers by XIRR")
        
        if not holdings_df.empty:
            top_10 = holdings_df.nlargest(10, 'xirr')
            
            fig_top = go.Figure(go.Bar(
                x=top_10['xirr'],
                y=top_10['scheme_name'].apply(lambda x: x[:40]),
                orientation='h',
                marker=dict(
                    color=top_10['xirr'],
                    colorscale='RdYlGn',
                    showscale=False
                ),
                text=top_10['xirr'].apply(lambda x: f"{x:.1f}%"),
                textposition='auto'
            ))
            
            fig_top.update_layout(
                xaxis_title="XIRR %",
                yaxis_title="",
                height=400,
                showlegend=False,
                margin=dict(l=0, r=0, t=0, b=0)
            )
            
            st.plotly_chart(fig_top, use_container_width=True)
    
    with col_right:
        # Asset Allocation Pie Chart
        st.subheader("📊 Asset Allocation")
        
        # Calculate allocation
        type_allocation = holdings_df.groupby('type')['current_value'].sum()
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=type_allocation.index,
            values=type_allocation.values,
            hole=0.4,
            marker=dict(colors=px.colors.qualitative.Set3)
        )])
        
        fig_pie.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=True
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    st.markdown("---")
    
    # Active SIPs Section
    if sips:
        st.subheader("💰 Active SIPs")
        
        sip_df = pd.DataFrame(sips)
        
        # SIP Summary Metrics
        sip_col1, sip_col2, sip_col3, sip_col4 = st.columns(4)
        
        with sip_col1:
            monthly_sips = sum(s['sip_amount'] for s in sips if s.get('frequency') == 'Monthly')
            st.metric("Monthly SIP Amount", format_currency(monthly_sips))
        
        with sip_col2:
            total_sip_invested = sum(s.get('total_invested', 0) for s in sips)
            st.metric("Total SIP Invested", format_currency(total_sip_invested))
        
        with sip_col3:
            total_installments = sum(s.get('total_installments', 0) for s in sips)
            st.metric("Total Installments", total_installments)
        
        with sip_col4:
            st.metric("Active SIPs", len(sips))
        
        # SIP Details Table
        st.markdown("#### SIP Details")
        sip_df = pd.DataFrame(sips)
        
        if not sip_df.empty:
            # Prepare display columns based on what's available
            base_sip_columns = ['scheme_name', 'sip_amount', 'frequency']
            optional_sip_columns = []
            
            if 'last_installment_date' in sip_df.columns:
                optional_sip_columns.append('last_installment_date')
            if 'next_installment_date' in sip_df.columns:
                optional_sip_columns.append('next_installment_date')
            if 'total_installments' in sip_df.columns:
                optional_sip_columns.append('total_installments')
            if 'broker' in sip_df.columns:
                optional_sip_columns.append('broker')
            
            # Filter for columns that actually exist in sip_df
            display_sip_columns = [col for col in (base_sip_columns + optional_sip_columns) if col in sip_df.columns]
            sip_display = sip_df[display_sip_columns].copy()
            
            # Rename columns
            column_renames = {
                'scheme_name': 'Fund Name',
                'sip_amount': 'SIP Amount',
                'frequency': 'Frequency',
                'last_installment_date': 'Last Date',
                'next_installment_date': 'Next Date',
                'total_installments': 'Installments',
                'broker': 'Broker'
            }
            sip_display.columns = [column_renames.get(col, col) for col in sip_display.columns]
            
            # Format SIP amount
            if 'SIP Amount' in sip_display.columns:
                sip_display['SIP Amount'] = sip_display['SIP Amount'].apply(
                    lambda x: f"₹{x:,.0f}" if pd.notna(x) else "-"
                )
            if 'Next Date' in sip_display.columns:
                sip_display['Next Date'] = pd.to_datetime(sip_display['Next Date'], errors='coerce').dt.strftime('%d-%b-%Y').fillna('N/A')
            if 'Last Date' in sip_display.columns:
                sip_display['Last Date'] = pd.to_datetime(sip_display['Last Date'], errors='coerce').dt.strftime('%d-%b-%Y').fillna('N/A')
            
            st.dataframe(sip_display, use_container_width=True, hide_index=True)
        else:
            st.info("No active SIPs found")
        
        st.markdown("---")
    
    # Broker Analysis Section
    if brokers:
        st.subheader("🤝 Broker Analysis")
        
        broker_col1, broker_col2 = st.columns([2, 1])
        
        with broker_col1:
            # Broker Investment Bar Chart
            broker_names = list(brokers.keys())
            broker_investments = [brokers[b]['total_invested'] for b in broker_names]
            
            fig_broker = go.Figure(go.Bar(
                x=broker_investments,
                y=broker_names,
                orientation='h',
                marker=dict(color='#3b82f6'),
                text=[format_currency(v) for v in broker_investments],
                textposition='auto'
            ))
            
            fig_broker.update_layout(
                xaxis_title="Total Invested (₹)",
                yaxis_title="",
                height=300,
                showlegend=False
            )
            
            st.plotly_chart(fig_broker, use_container_width=True)
        
        with broker_col2:
            # Broker Allocation Pie
            fig_broker_pie = go.Figure(data=[go.Pie(
                labels=broker_names,
                values=broker_investments,
                hole=0.4
            )])
            
            fig_broker_pie.update_layout(
                height=300,
                margin=dict(l=0, r=0, t=0, b=0)
            )
            
            st.plotly_chart(fig_broker_pie, use_container_width=True)
        
        # Broker Details Table
        broker_data = []
        for broker, info in brokers.items():
            broker_data.append({
                'Broker': broker,
                'Total Invested': format_currency(info['total_invested']),
                'Schemes': info['scheme_count'],
                'Transactions': info['transaction_count'],
                'First Transaction': info.get('first_transaction', 'N/A'),
                'Last Transaction': info.get('last_transaction', 'N/A')
            })
        
        st.dataframe(broker_data, use_container_width=True, hide_index=True)
        
        st.markdown("---")
    
    # Category-wise Performance
    st.subheader("📂 Category-wise Performance")
    
    if not holdings_df.empty:
        category_summary = holdings_df.groupby('type').agg({
            'current_value': 'sum',
            'cost_value': 'sum',
            'gain_loss': 'sum'
        }).reset_index()
        
        category_summary['return_pct'] = (
            (category_summary['gain_loss'] / category_summary['cost_value']) * 100
        )
        
        category_summary.columns = ['Category', 'Current Value', 'Invested', 'Gain/Loss', 'Return %']
        category_summary['Current Value'] = category_summary['Current Value'].apply(format_currency)
        category_summary['Invested'] = category_summary['Invested'].apply(format_currency)
        category_summary['Gain/Loss'] = category_summary['Gain/Loss'].apply(format_currency)
        category_summary['Return %'] = category_summary['Return %'].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(category_summary, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Top Gainers and Losers
    st.subheader("📈 Top Gainers & Losers")
    
    if not holdings_df.empty:
        sorted_by_return = holdings_df.sort_values('gain_loss_percent', ascending=False)
        
        col_gain, col_loss = st.columns(2)
        
        with col_gain:
            st.markdown("**✅ Top 5 Gainers**")
            top_5 = sorted_by_return.head(5)
            
            for _, row in top_5.iterrows():
                with st.container():
                    st.success(
                        f"**{row['scheme_name'][:45]}**  \n"
                        f"+{row['gain_loss_percent']:.2f}% • XIRR: {row['xirr']:.2f}% • "
                        f"{format_currency(row['current_value'])}"
                    )
        
        with col_loss:
            st.markdown("**❌ Top 5 Losers**")
            bottom_5 = sorted_by_return.tail(5)
            
            for _, row in bottom_5.iterrows():
                with st.container():
                    st.error(
                        f"**{row['scheme_name'][:45]}**  \n"
                        f"{row['gain_loss_percent']:.2f}% • XIRR: {row['xirr']:.2f}% • "
                        f"{format_currency(row['current_value'])}"
                    )
    
    # Footer
    st.markdown("---")
    st.caption(f"Last updated: {portfolio.get('last_updated', 'Never')} • Data source: {portfolio.get('data_source', 'Unknown')}")

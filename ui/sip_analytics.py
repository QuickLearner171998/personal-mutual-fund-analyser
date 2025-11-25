"""
Dedicated SIP Analytics Dashboard
Detailed analysis of Systematic Investment Plans
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, date, timedelta
from database.json_store import PortfolioStore
from utils.formatters import format_currency
from calculations.returns import calculate_sip_returns


def render_sip_dashboard():
    st.markdown('<div class="main-header">💰 SIP Analytics</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Load data
    try:
        store = PortfolioStore()
        data = store.get_complete_data()
        sips = data.get('sips', [])
        transactions = data.get('transactions', [])
        portfolio = data.get('portfolio', {})
    except Exception as e:
        st.error(f"❌ Error loading SIP data: {str(e)}")
        return
    
    if not sips:
        st.info("📊 No active SIPs found in your portfolio")
        return
    
    # SIP Overview Metrics
    st.subheader("📊 SIP Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_sip_invested = sum(s.get('total_invested', 0) for s in sips)
    monthly_outflow = sum(s['sip_amount'] for s in sips if s.get('frequency') == 'Monthly')
    total_installments = sum(s.get('total_installments', 0) for s in sips)
    
    with col1:
        st.metric("Active SIPs", len(sips))
    
    with col2:
        st.metric("Monthly Outflow", format_currency(monthly_outflow))
    
    with col3:
        st.metric("Total SIP Invested", format_currency(total_sip_invested))
    
    with col4:
        st.metric("Total Installments", total_installments)
    
    st.markdown("---")
    
    # SIP Calendar - Upcoming Installments
    st.subheader("📅 Upcoming SIP Installments")
    
    # Sort by next installment date
    sips_sorted = sorted(sips, key=lambda x: x.get('next_installment_date', '9999-12-31'))
    
    # Show next 30 days
    today = date.today()
    next_30_days = today + timedelta(days=30)
    
    upcoming_sips = [
        s for s in sips_sorted 
        if s.get('next_installment_date') and 
        today <= datetime.fromisoformat(str(s['next_installment_date'])).date() <= next_30_days
    ]
    
    if upcoming_sips:
        for sip in upcoming_sips:
            next_date = datetime.fromisoformat(str(sip['next_installment_date'])).date()
            days_until = (next_date - today).days
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**{sip['scheme_name'][:50]}**")
            
            with col2:
                st.write(f"{format_currency(sip['sip_amount'])}")
            
            with col3:
                if days_until == 0:
                    st.warning("Today")
                elif days_until <= 7:
                    st.info(f"In {days_until} days")
                else:
                    st.write(next_date.strftime('%d-%b-%Y'))
    else:
        st.info("No SIP installments in the next 30 days")
    
    st.markdown("---")
    
    # SIP Details Table
    st.subheader("📋 SIP Details")
    
    sip_df = pd.DataFrame(sips)
    
    display_df = sip_df[[
        'scheme_name', 'sip_amount', 'frequency', 'start_date',
        'last_installment_date', 'next_installment_date', 
        'total_installments', 'total_invested', 'broker'
    ]].copy()
    
    display_df.columns = [
        'Fund Name', 'SIP Amount', 'Frequency', 'Start Date',
        'Last Installment', 'Next Installment', 
        'Installments', 'Total Invested', 'Broker'
    ]
    
    # Format columns
    display_df['SIP Amount'] = display_df['SIP Amount'].apply(format_currency)
    display_df['Total Invested'] = display_df['Total Invested'].apply(format_currency)
    display_df['Start Date'] = pd.to_datetime(display_df['Start Date']).dt.strftime('%d-%b-%Y')
    display_df['Last Installment'] = pd.to_datetime(display_df['Last Installment']).dt.strftime('%d-%b-%Y')
    display_df['Next Installment'] = pd.to_datetime(display_df['Next Installment']).dt.strftime('%d-%b-%Y')
    
    st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)
    
    st.markdown("---")
    
    # SIP Performance Analysis
    st.subheader("📈 SIP Performance")
    
    # Calculate SIP returns for each fund
    sip_performance = []
    
    for sip in sips:
        # Get SIP transactions for this fund
        sip_txns = [
            t for t in transactions
            if t.get('scheme_name') == sip['scheme_name']
            and t.get('folio_number') == sip['folio_number']
            and t.get('transaction_type') == 'sip'
        ]
        
        # Get current value from portfolio
        holdings = portfolio.get('holdings', [])
        current_value = 0
        for h in holdings:
            if (h.get('scheme_name') == sip['scheme_name'] and 
                h.get('folio_number') == sip['folio_number']):
                current_value = h.get('current_value', 0)
                break
        
        if sip_txns:
            returns = calculate_sip_returns(sip_txns, current_value)
            
            if returns:
                sip_performance.append({
                    'scheme_name': sip['scheme_name'],
                    'total_invested': returns.get('total_invested', 0),
                    'current_value': returns.get('current_value', 0),
                    'absolute_return': returns.get('absolute_return', 0),
                    'absolute_return_pct': returns.get('absolute_return_pct', 0),
                    'xirr': returns.get('xirr', 0),
                    'installments': returns.get('total_installments', 0)
                })
    
    if sip_performance:
        perf_df = pd.DataFrame(sip_performance)
        
        # Display performance table
        display_perf = perf_df.copy()
        display_perf.columns = [
            'Fund Name', 'Invested', 'Current Value', 
            'Absolute Return', 'Return %', 'XIRR %', 'Installments'
        ]
        
        display_perf['Invested'] = display_perf['Invested'].apply(format_currency)
        display_perf['Current Value'] = display_perf['Current Value'].apply(format_currency)
        display_perf['Absolute Return'] = display_perf['Absolute Return'].apply(format_currency)
        display_perf['Return %'] = display_perf['Return %'].apply(lambda x: f"{x:.2f}%")
        display_perf['XIRR %'] = display_perf['XIRR %'].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(display_perf, use_container_width=True, hide_index=True)
        
        # SIP Performance Chart
        st.markdown("#### SIP XIRR Comparison")
        
        fig_sip_xirr = go.Figure(go.Bar(
            x=perf_df['xirr'],
            y=perf_df['scheme_name'].apply(lambda x: x[:40]),
            orientation='h',
            marker=dict(
                color=perf_df['xirr'],
                colorscale='RdYlGn',
                showscale=False
            ),
            text=perf_df['xirr'].apply(lambda x: f"{x:.1f}%"),
            textposition='auto'
        ))
        
        fig_sip_xirr.update_layout(
            xaxis_title="XIRR %",
            yaxis_title="",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig_sip_xirr, use_container_width=True)
    
    st.markdown("---")
    
    # SIP Contribution Timeline
    st.subheader("📊 SIP Contribution Timeline")
    
    # Get all SIP transactions
    all_sip_txns = [t for t in transactions if t.get('transaction_type') == 'sip']
    
    if all_sip_txns:
        # Group by month
        sip_timeline = pd.DataFrame(all_sip_txns)
        sip_timeline['month'] = pd.to_datetime(sip_timeline['trade_date']).dt.to_period('M')
        
        monthly_sip = sip_timeline.groupby('month')['amount'].apply(lambda x: abs(x).sum()).reset_index()
        monthly_sip['month'] = monthly_sip['month'].astype(str)
        
        # Plot timeline
        fig_timeline = go.Figure(go.Bar(
            x=monthly_sip['month'],
            y=monthly_sip['amount'],
            marker=dict(color='#10b981'),
            text=monthly_sip['amount'].apply(lambda x: format_currency(x)),
            textposition='outside'
        ))
        
        fig_timeline.update_layout(
            xaxis_title="Month",
            yaxis_title="SIP Amount (₹)",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Footer
    st.caption("💡 Tip: Regular SIP investments help in rupee cost averaging and building wealth over time")

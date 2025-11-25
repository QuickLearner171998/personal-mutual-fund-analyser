"""
CAS PDF Upload Interface
"""
import streamlit as st
import sys
import os
from pathlib import Path
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from enrichment.nav_fetcher import NAVFetcher
from calculations.returns import calculate_allocation, calculate_absolute_return
from database.json_store import PortfolioStore
from cas_import.custom_cas_parser import CustomCASParser

def render_cas_upload():
    st.markdown('<div class="main-header">📁 Upload CAS PDF</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("""
    ### How to get your CAS PDF:
    1. Visit [MF Central](https://mfcentral.com) or [CAMS](https://www.camsonline.com)
    2. Login with your PAN
    3. Download Consolidated Account Statement (CAS)
    4. Upload the PDF below
    
    **Note:** Most CAS PDFs are **not password protected**. Leave password blank.
    """)
    
    uploaded_file = st.file_uploader(
        "Choose CAS PDF file",
        type=['pdf'],
        help="Upload your Consolidated Account Statement PDF"
    )
    
    if uploaded_file and st.button("🚀 Parse & Analyze CAS", type="primary", use_container_width=True):
        with st.spinner("Processing your CAS PDF... This may take a minute for large files."):
            try:
                # Save uploaded file temporarily
                temp_path = f"data/temp_{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                # Parse CAS using ENHANCED parser (extracts ALL transactions)
                st.info("Step 1/4: Parsing CAS PDF...")
                from cas_import.enhanced_cas_parser import EnhancedCASParser
                
                parser = EnhancedCASParser(temp_path)
                cas_data = parser.parse()
                
                # Extract data
                st.info("Step 2/4: Extracting holdings and transactions...")
                holdings = cas_data.get('holdings', [])
                transactions = cas_data.get('transactions', [])
                summary_data = cas_data.get('summary', {})
                investor_info = cas_data.get('investor_info', {})
                
                st.success(f"✓ Found {len(holdings)} holdings and {len(transactions)} transactions")
                
                
                # Enhanced parser already calculated everything!
                st.info("Step 3/4: Validating data...")
                enriched_holdings = holdings
                
                # Calculate portfolio metrics (already done by parser)
                st.info("Step 4/4: Preparing portfolio data...")
                total_value = summary_data.get('total_value', 0)
                total_invested = summary_data.get('total_invested', 0)
                total_gain = summary_data.get('total_gain', 0)
                
                allocation = calculate_allocation(enriched_holdings)
                
                # Prepare portfolio data
                statement_period = cas_data.get('statement_period', {})
                portfolio_data = {
                    'investor_name': investor_info.get('name', ''),
                    'pan': investor_info.get('pan', ''),
                    'email': investor_info.get('email', ''),
                    'mobile': investor_info.get('mobile', ''),
                    'total_value': total_value,
                    'total_invested': total_invested,
                    'total_gain': total_gain,
                    'total_gain_percent': (total_gain / total_invested * 100) if total_invested > 0 else 0,
                    'xirr': 0,  # TODO: Calculate XIRR from transactions
                    'holdings': enriched_holdings,
                    'allocation': allocation,
                    'statement_period_from': statement_period.get('from'),
                    'statement_period_to': statement_period.get('to')
                }
                
                # Save to JSON file (NO MONGODB)
                store = PortfolioStore()
                store.save_portfolio(portfolio_data)
                store.save_transactions(transactions)
                
                # Save historical snapshot
                from utils.history_tracker import tracker
                tracker.save_snapshot()
                
                # Index in FAISS for RAG
                try:
                    from vector_db.portfolio_indexer import index_portfolio_data
                    index_portfolio_data(portfolio_data)
                    print("✓ Indexed portfolio in FAISS")
                except Exception as e:
                    print(f"Warning: FAISS indexing failed: {e}")
                
                st.success("✅ Portfolio successfully analyzed and saved!")
                
                # Show summary
                st.markdown("### 📊 Portfolio Summary")
                from utils.formatters import format_currency
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Value", format_currency(total_value))
                with col2:
                    st.metric("Total Invested", format_currency(total_invested))
                with col3:
                    gain_pct = portfolio_data['total_gain_percent']
                    st.metric("Gain/Loss", format_currency(total_gain), delta=f"{gain_pct:.2f}%")
                
                st.info("✨ Go to **📊 Dashboard** to view your complete portfolio analysis!")
                
                # Cleanup
                os.remove(temp_path)
                
            except Exception as e:
                st.error(f"❌ Error processing CAS: {str(e)}")
                st.exception(e)

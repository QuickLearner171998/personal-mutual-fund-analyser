"""
MF Central File Upload Interface
Upload and process MF Central JSON files
"""
import streamlit as st
import json
import tempfile
import os
from datetime import datetime

from cas_import.mf_central_parser import MFCentralParser
from database.json_store import PortfolioStore

# Import new processing function
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from ui.cas_upload_v2 import process_mf_central_files_v2


def render_upload_page():
    st.markdown('<div class="main-header">📁 Upload MF Central Data</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Instructions
    with st.expander("📖 How to Download Files from MF Central", expanded=True):
        st.markdown("""
        ### New Simplified Workflow (2 Files Only!)
        
        We now use **Excel + Transaction JSON** for complete portfolio analysis.
        
        #### File 1: Excel Detailed Report ⭐ (PRIMARY SOURCE)
        - Navigate to: **MF Central → Reports → Detailed Report**
        - Select date range (recommend: All time or Last 3 years)
        - Click **Download as Excel** button
        - You'll get: `cas_detailed_report_YYYY_MM_DD_HHMMSS.xlsx`
        - **This contains**: All holdings, current values, invested amounts, gains
        
        #### File 2: Transaction Details Statement (FOR SIPs & BROKERS)
        - Navigate to: **Transactions → Transaction Details Statement**
        - Select date range (recommend: All time)
        - Click **Download** button
        - You'll get a **ZIP file**
        - **Extract the ZIP** and find: `AS*.json`
        - **This contains**: Transaction history, SIP details, broker information
        
        ### Why Only 2 Files?
        
        ✅ **Excel** has the most current and complete holdings data (43 funds)  
        ✅ **Transaction JSON** provides SIP patterns and broker details  
        ❌ **Old workflow** required 3 JSON files (now simplified!)
        
        ### Important Notes:
        - ✅ Excel is downloaded directly (no ZIP extraction needed)
        - ✅ Transaction JSON must be extracted from ZIP
        - ✅ Both files must be from the same time period
        - ✅ Upload both files for complete analysis
        """)
    
    st.markdown("---")
    
    # File upload section
    st.subheader("📤 Upload Your Files")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**1. Excel Report** ⭐")
        st.caption("cas_detailed_report*.xlsx")
        excel_file = st.file_uploader(
            "Upload Excel",
            type=['xlsx'],
            key="excel",
            help="MF Central → Reports → Detailed Report (Excel)"
        )
    
    with col2:
        st.markdown("**2. Transactions**")
        st.caption("AS*.json")
        transaction_file = st.file_uploader(
            "Upload Transactions",
            type=['json'],
            key="transactions",
            help="Extract from Transaction Details zip"
        )
    
    with col3:
        st.markdown("**3. XIRR Data**")
        st.caption("*IMBPF*.json")
        xirr_file = st.file_uploader(
            "Upload XIRR JSON",
            type=['json'],
            key="xirr",
            help="Detailed report JSON with XIRR"
        )
    
    st.markdown("---")
    
    # Process button
    if excel_file and transaction_file and xirr_file:
        if st.button("🚀 Process Files", type="primary", use_container_width=True):
            process_mf_central_files_v2(excel_file, transaction_file, xirr_file)
    else:
        st.info("👆 Please upload all 3 files to continue")
        
        # Show which files are uploaded
        status_col1, status_col2, status_col3 = st.columns(3)
        with status_col1:
            if excel_file:
                st.success("✅ Uploaded")
            else:
                st.warning("⏳ Pending")
        with status_col2:
            if transaction_file:
                st.success("✅ Uploaded")
            else:
                st.warning("⏳ Pending")
        with status_col3:
            if xirr_file:
                st.success("✅ Uploaded")
            else:
                st.warning("⏳ Pending")


def process_mf_central_files(consolidated_file, transaction_file, detailed_file):
    """Process uploaded MF Central files"""
    
    try:
        with st.spinner("📊 Processing your portfolio data..."):
            # Create progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Load JSON files
            status_text.text("Loading JSON files...")
            progress_bar.progress(10)
            
            consolidated_data = json.load(consolidated_file)
            transaction_data = json.load(transaction_file)
            detailed_data = json.load(detailed_file)
            
            # Step 2: Validate data
            status_text.text("Validating data structure...")
            progress_bar.progress(20)
            
            from core.portfolio_processor import validate_mf_central_data
            is_valid, error = validate_mf_central_data(
                consolidated_data,
                transaction_data,
                detailed_data
            )
            
            if not is_valid:
                st.error(f"❌ Validation Error: {error}")
                return
            
            # Step 3: Parse and save data
            status_text.text("Parsing and saving portfolio data...")
            progress_bar.progress(40)
            
            from core.portfolio_processor import process_mf_central_data, get_portfolio_summary, get_transaction_summary
            
            portfolio_data, transactions = process_mf_central_data(
                consolidated_data,
                transaction_data,
                detailed_data,
                save_to_db=True,
                index_for_qa=True
            )
            
            # Complete
            progress_bar.progress(100)
            status_text.text("✅ Processing complete!")
            
            # Show summary
            st.success("🎉 Portfolio data processed successfully!")
            
            # Display summary
            st.markdown("---")
            st.subheader("📊 Portfolio Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Value",
                    f"₹{summary['total_value']:,.2f}"
                )
            
            with col2:
                st.metric(
                    "Total Invested",
                    f"₹{summary['total_invested']:,.2f}"
                )
            
            with col3:
                st.metric(
                    "Total Gain",
                    f"₹{summary['total_gain']:,.2f}",
                    delta=f"{summary['total_gain_percent']:.2f}%"
                )
            
            with col4:
                st.metric(
                    "Portfolio XIRR",
                    f"{summary['xirr']:.2f}%"
                )
            
            # Additional stats
            st.markdown("---")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.info(f"**{summary['num_funds']}** Funds")
            
            with col2:
                st.info(f"**{summary['num_aggregated_funds']}** After Aggregation")
            
            with col3:
                st.info(f"**{summary['num_active_sips']}** Active SIPs")
            
            with col4:
                st.info(f"**{summary['num_brokers']}** Brokers")
            
            # Transaction summary
            st.markdown("---")
            st.subheader("📝 Transaction Summary")
            
            txn_col1, txn_col2, txn_col3 = st.columns(3)
            
            with txn_col1:
                st.metric("Total Transactions", txn_summary['total'])
            
            with txn_col2:
                st.metric("Purchase Transactions", txn_summary['by_type'].get('purchase', 0))
            
            with txn_col3:
                st.metric("SIP Transactions", txn_summary['by_type'].get('sip', 0))
            
            # Broker summary
            broker_info = portfolio_data.get('broker_info', {})
            if broker_info:
                st.markdown("---")
                st.subheader("🤝 Broker Summary")
                
                broker_data = []
                for broker, info in broker_info.items():
                    broker_data.append({
                        'Broker': broker,
                        'Total Invested': f"₹{info['total_invested']:,.2f}",
                        'Schemes': info['scheme_count'],
                        'Transactions': info['transaction_count']
                    })
                
                st.dataframe(broker_data, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.info("👈 Navigate to **Dashboard** to view detailed analytics!")
            
    except json.JSONDecodeError as e:
        st.error(f"❌ Invalid JSON file: {str(e)}")
    except Exception as e:
        st.error(f"❌ Error processing files: {str(e)}")
        st.exception(e)

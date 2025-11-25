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
from vector_db.portfolio_indexer import PortfolioIndexer


def render_upload_page():
    st.markdown('<div class="main-header">📁 Upload MF Central Data</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Instructions
    with st.expander("📖 How to Download Files from MF Central", expanded=True):
        st.markdown("""
        ### Step-by-Step Guide:
        
        1. **Visit MF Central**: Go to [mfcentral.com](https://mfcentral.com)
        2. **Login**: Use your credentials to login
        3. **Download Required Files**:
        
        #### File 1: CONSOLIDATED PORTFOLIO STATEMENT
        - Navigate to: **Portfolio → Consolidated Portfolio Statement**
        - Click **Download** button
        - You'll get a **ZIP file** (e.g., `CCJN4KTLB310840997771IMBAS199068013.zip`)
        - **Extract the ZIP** and find the JSON file: `CurrentValuationAS*.json`
        
        #### File 2: TRANSACTION DETAILS STATEMENT
        - Navigate to: **Transactions → Transaction Details Statement**
        - Select date range (recommend: All time)
        - Click **Download** button
        - You'll get a **ZIP file** (same as above or separate)
        - **Extract the ZIP** and find the JSON file: `AS*.json`
        
        #### File 3: Detailed Report with XIRR
        - Navigate to: **Reports → Detailed Report**
        - This will show a table with XIRR values
        - Look for **Download as JSON** option
        - You'll get a JSON file like: `70910727520211641ZF683740997FF11IMBPF199067986.json`
        
        ### Important Notes:
        - ✅ All files must be in **JSON format**
        - ✅ Extract ZIP files before uploading
        - ✅ File names may vary but structure remains same
        - ✅ Upload all 3 files for complete analysis
        """)
    
    st.markdown("---")
    
    # File upload section
    st.subheader("📤 Upload Your Files")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**1. Current Valuation**")
        st.caption("CurrentValuation*.json")
        consolidated_file = st.file_uploader(
            "Upload Consolidated Portfolio",
            type=['json'],
            key="consolidated",
            help="Extract from CONSOLIDATED PORTFOLIO STATEMENT zip"
        )
    
    with col2:
        st.markdown("**2. Transaction Details**")
        st.caption("AS*.json")
        transaction_file = st.file_uploader(
            "Upload Transaction Details",
            type=['json'],
            key="transactions",
            help="Extract from TRANSACTION DETAILS STATEMENT zip"
        )
    
    with col3:
        st.markdown("**3. Detailed Report**")
        st.caption("*IMBPF*.json")
        detailed_file = st.file_uploader(
            "Upload Detailed Report",
            type=['json'],
            key="detailed",
            help="Detailed report with XIRR data"
        )
    
    st.markdown("---")
    
    # Process button
    if consolidated_file and transaction_file and detailed_file:
        if st.button("🚀 Process Files", type="primary", use_container_width=True):
            process_mf_central_files(consolidated_file, transaction_file, detailed_file)
    else:
        st.info("👆 Please upload all 3 files to continue")
        
        # Show which files are uploaded
        status_col1, status_col2, status_col3 = st.columns(3)
        with status_col1:
            if consolidated_file:
                st.success("✅ Uploaded")
            else:
                st.warning("⏳ Pending")
        with status_col2:
            if transaction_file:
                st.success("✅ Uploaded")
            else:
                st.warning("⏳ Pending")
        with status_col3:
            if detailed_file:
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
            
            validation_result = validate_json_structure(
                consolidated_data, 
                transaction_data, 
                detailed_data
            )
            
            if not validation_result['valid']:
                st.error(f"❌ Validation Error: {validation_result['error']}")
                return
            
            # Step 3: Parse data
            status_text.text("Parsing portfolio data...")
            progress_bar.progress(30)
            
            parser = MFCentralParser()
            portfolio_data = parser.build_portfolio_data(
                consolidated_data,
                transaction_data,
                detailed_data
            )
            
            # Step 4: Save to database
            status_text.text("Saving to database...")
            progress_bar.progress(60)
            
            store = PortfolioStore()
            store.save_complete_data(
                portfolio=portfolio_data,
                transactions=parser.transaction_data,
                sips=portfolio_data.get('active_sips', []),
                broker_info=portfolio_data.get('broker_info', {}),
                aggregation_map=portfolio_data.get('aggregation_map', {})
            )
            
            # Step 5: Index for Q&A
            status_text.text("Indexing for Q&A chatbot...")
            progress_bar.progress(80)
            
            try:
                indexer = PortfolioIndexer()
                indexer.index_portfolio(portfolio_data, parser.transaction_data)
            except Exception as e:
                st.warning(f"⚠️ Q&A indexing skipped: {str(e)}")
            
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
                    f"₹{portfolio_data['total_value']:,.2f}"
                )
            
            with col2:
                st.metric(
                    "Total Invested",
                    f"₹{portfolio_data['total_invested']:,.2f}"
                )
            
            with col3:
                st.metric(
                    "Total Gain",
                    f"₹{portfolio_data['total_gain']:,.2f}",
                    delta=f"{portfolio_data['total_gain_percent']:.2f}%"
                )
            
            with col4:
                st.metric(
                    "Portfolio XIRR",
                    f"{portfolio_data.get('xirr', 0):.2f}%"
                )
            
            # Additional stats
            st.markdown("---")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.info(f"**{portfolio_data['num_funds']}** Funds")
            
            with col2:
                st.info(f"**{portfolio_data['num_aggregated_funds']}** After Aggregation")
            
            with col3:
                st.info(f"**{portfolio_data['num_active_sips']}** Active SIPs")
            
            with col4:
                st.info(f"**{portfolio_data['num_brokers']}** Brokers")
            
            # Transaction summary
            st.markdown("---")
            st.subheader("📝 Transaction Summary")
            
            txn_types = {}
            for txn in parser.transaction_data:
                txn_type = txn['transaction_type']
                txn_types[txn_type] = txn_types.get(txn_type, 0) + 1
            
            txn_col1, txn_col2, txn_col3 = st.columns(3)
            
            with txn_col1:
                st.metric("Total Transactions", len(parser.transaction_data))
            
            with txn_col2:
                st.metric("Purchase Transactions", txn_types.get('purchase', 0))
            
            with txn_col3:
                st.metric("SIP Transactions", txn_types.get('sip', 0))
            
            # Broker summary
            if portfolio_data.get('broker_info'):
                st.markdown("---")
                st.subheader("🤝 Broker Summary")
                
                broker_data = []
                for broker, info in portfolio_data['broker_info'].items():
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


def validate_json_structure(consolidated_data, transaction_data, detailed_data):
    """Validate JSON structure"""
    
    try:
        # Check consolidated data
        if 'dtTrxnResult' not in consolidated_data:
            return {'valid': False, 'error': 'Consolidated file missing dtTrxnResult'}
        
        if not consolidated_data['dtTrxnResult']:
            return {'valid': False, 'error': 'Consolidated file has no holdings'}
        
        # Check transaction data
        if 'dtTrxnResult' not in transaction_data:
            return {'valid': False, 'error': 'Transaction file missing dtTrxnResult'}
        
        # Check detailed data
        if not isinstance(detailed_data, list):
            return {'valid': False, 'error': 'Detailed report should be a list'}
        
        if not detailed_data:
            return {'valid': False, 'error': 'Detailed report is empty'}
        
        # Check required fields in first entry
        required_consolidated_fields = ['Scheme', 'Folio', 'Unit Balance', 'Current Value(Rs.)']
        first_holding = consolidated_data['dtTrxnResult'][0]
        
        for field in required_consolidated_fields:
            if field not in first_holding:
                return {'valid': False, 'error': f'Missing field in consolidated data: {field}'}
        
        # Check detailed report fields
        required_detailed_fields = ['Scheme', 'Folio', 'CurrentValue', 'Annualised XIRR']
        first_detailed = detailed_data[0]
        
        for field in required_detailed_fields:
            if field not in first_detailed:
                return {'valid': False, 'error': f'Missing field in detailed report: {field}'}
        
        return {'valid': True}
        
    except Exception as e:
        return {'valid': False, 'error': str(e)}

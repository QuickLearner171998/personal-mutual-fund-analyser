def process_mf_central_files_v2(excel_file, transaction_file, xirr_file):
    """Process uploaded MF Central files (Excel + Transaction JSON + XIRR JSON)"""
    
    try:
        with st.spinner("📊 Processing your portfolio data..."):
            # Create progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Save uploaded files temporarily
            status_text.text("Saving uploaded files...")
            progress_bar.progress(10)
            
            import tempfile
            import os
            
            with tempfile.TemporaryDirectory() as tmpdir:
                # Save Excel
                excel_path = os.path.join(tmpdir, "portfolio.xlsx")
                with open(excel_path, 'wb') as f:
                    f.write(excel_file.read())
                
                # Save transaction JSON
                txn_path = os.path.join(tmpdir, "transactions.json")
                with open(txn_path, 'wb') as f:
                    f.write(transaction_file.read())
                
                # Step 2: Process data
                status_text.text("Processing portfolio data...")
                progress_bar.progress(30)
                
                from core.unified_processor import process_mf_central_complete
                
                portfolio_data = process_mf_central_complete(
                    excel_path,
                    txn_path
                )
                
                # Step 3: Save to database
                status_text.text("Saving to database...")
                progress_bar.progress(70)
                
                from database.json_store import PortfolioStore
                
                store = PortfolioStore()
                store.save_complete_data(
                    portfolio=portfolio_data,
                    transactions=[],  # Not storing full transaction history
                    sips=portfolio_data.get('active_sips', []),
                    broker_info=portfolio_data.get('broker_info', {}),
                    aggregation_map={}
                )
                
                # Step 4: Index for Q&A
                status_text.text("Indexing for Q&A chatbot...")
                progress_bar.progress(90)
                
                try:
                    from vector_db.portfolio_indexer import index_portfolio_data
                    index_portfolio_data(portfolio_data)
                except Exception as e:
                    st.warning(f"⚠️ Q&A indexing skipped: {str(e)}")
                
                # Complete
                progress_bar.progress(100)
                status_text.text("✅ Processing complete!")
            
            # Show summary
            st.success("🎉 Portfolio data processed successfully!")
            
            # Display summary using shared function
            from core.portfolio_processor import get_portfolio_summary, get_transaction_summary
            
            summary = get_portfolio_summary(portfolio_data)
            
            # Display summary
            st.markdown("---")
            st.subheader("📊 Portfolio Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Value", f"₹{summary['total_value']:,.2f}")
            
            with col2:
                st.metric("Total Invested", f"₹{summary['total_invested']:,.2f}")
            
            with col3:
                st.metric(
                    "Total Gain",
                    f"₹{summary['total_gain']:,.2f}",
                    delta=f"{summary['total_gain_percent']:.2f}%"
                )
            
            with col4:
                st.metric("Active SIPs", summary['num_active_sips'])
            
            # Additional stats
            st.markdown("---")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info(f"**{summary['num_funds']}** Total Funds")
            
            with col2:
                st.info(f"**{summary['num_active_sips']}** Active SIPs")
            
            with col3:
                st.info(f"**{summary['num_brokers']}** Brokers")
            
            # SIP summary
            if portfolio_data.get('active_sips'):
                st.markdown("---")
                st.subheader("🔄 Active SIPs")
                
                sip_data = []
                for sip in portfolio_data['active_sips'][:10]:
                    sip_data.append({
                        'Fund': sip['scheme_name'][:40],
                        'Amount': f"₹{sip['sip_amount']:,.0f}",
                        'Frequency': sip['frequency'],
                        'Broker': sip['broker']
                    })
                
                st.dataframe(sip_data, use_container_width=True, hide_index=True)
            
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

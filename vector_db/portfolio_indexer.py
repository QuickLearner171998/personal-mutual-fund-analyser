"""
Portfolio Indexer for FAISS - RAG Optimized
Stores raw, unprocessed data with complete metadata for LLM retrieval
Following best practices: minimal text processing, full structured data in metadata
"""
from vector_db.faiss_store import LocalVectorStore
from typing import Dict, List
import json
from datetime import date, datetime


def json_serial(obj):
    """
    JSON serializer for objects not serializable by default json code.
    Handles date and datetime objects.
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def index_portfolio_data(portfolio_data: Dict):
    """
    Index portfolio data for RAG (Retrieval Augmented Generation).
    
    Best Practices Implemented:
    1. Store RAW data in metadata without processing
    2. Create minimal descriptive text for embeddings
    3. Keep all structured information for filtering
    4. Index holdings, SIPs, and transactions separately
    5. Preserve complete context for LLM
    
    Args:
        portfolio_data: Complete portfolio dictionary
    """
    store = LocalVectorStore()
    
    # Clear existing data
    store.clear()
    
    texts = []
    metadatas = []
    
    # 1. INDEX PORTFOLIO SUMMARY (raw data)
    summary_text = (
        f"Portfolio Summary for {portfolio_data.get('investor_name', 'Investor')}: "
        f"{portfolio_data.get('num_funds', 0)} funds, "
        f"Total value ₹{portfolio_data.get('total_value', 0):,.0f}, "
        f"Total invested ₹{portfolio_data.get('total_invested', 0):,.0f}, "
        f"Returns {portfolio_data.get('total_gain_percent', 0):.2f}%, "
        f"XIRR {portfolio_data.get('xirr', 0):.2f}%"
    )
    texts.append(summary_text)
    metadatas.append({
        'type': 'portfolio_summary',
        'data': json.dumps({
            'investor_name': portfolio_data.get('investor_name', ''),
            'pan': portfolio_data.get('pan', ''),
            'total_value': portfolio_data.get('total_value', 0),
            'total_invested': portfolio_data.get('total_invested', 0),
            'total_gain': portfolio_data.get('total_gain', 0),
            'total_gain_percent': portfolio_data.get('total_gain_percent', 0),
            'xirr': portfolio_data.get('xirr', 0),
            'num_funds': portfolio_data.get('num_funds', 0),
            'num_active_sips': portfolio_data.get('num_active_sips', 0),
            'num_brokers': portfolio_data.get('num_brokers', 0),
            'data_source': portfolio_data.get('data_source', ''),
            'last_updated': portfolio_data.get('last_updated', '')
        })
    })
    
    # 2. INDEX EACH HOLDING (complete raw data)
    for idx, holding in enumerate(portfolio_data.get('holdings', [])):
        # Minimal descriptive text for embedding
        text = (
            f"{holding.get('scheme_name', 'Unknown Fund')} "
            f"({holding.get('amc', 'Unknown AMC')}) - "
            f"{holding.get('type', 'EQUITY')} fund - "
            f"Folio {holding.get('folio_number', '')} - "
            f"Current value ₹{holding.get('current_value', 0):,.0f}, "
            f"Invested ₹{holding.get('cost_value', 0):,.0f}, "
            f"Returns {holding.get('gain_loss_percent', 0):.2f}%, "
            f"XIRR {holding.get('xirr', 0):.2f}%"
        )
        
        texts.append(text)
        # Store COMPLETE raw holding data in metadata with enhanced filtering fields
        metadatas.append({
            'type': 'holding',
            'holding_id': f'holding_{idx}',
            'fund_category': holding.get('type', 'EQUITY'),  # EQUITY, DEBT, HYBRID
            'scheme_name': holding.get('scheme_name', ''),
            'amc': holding.get('amc', ''),
            'data': json.dumps(holding, default=json_serial)  # Complete unprocessed data
        })
    
    # 3. INDEX EACH SIP (complete raw data)
    for idx, sip in enumerate(portfolio_data.get('active_sips', [])):
        # Enhanced descriptive text for better SIP query matching
        is_active = sip.get('is_active', False)
        status = "Active SIP" if is_active else "Inactive SIP"
        frequency = sip.get('frequency', 'Monthly')
        
        # More query-friendly text for semantic search
        text = (
            f"{status} in {sip.get('scheme_name', 'Unknown Fund')} "
            f"({sip.get('amc', 'Unknown AMC')}) - "
            f"Folio: {sip.get('folio_number', '')} - "
            f"Investment: ₹{sip.get('sip_amount', 0):,.0f} {frequency} - "
            f"Installments: {sip.get('total_installments', 0)} completed - "
            f"Total SIP invested: ₹{sip.get('total_invested', 0):,.0f} - "
            f"Last payment: {sip.get('last_installment_date', 'Unknown')} - "
            f"Broker: {sip.get('broker', 'Direct')}"
        )
        
        texts.append(text)
        # Store COMPLETE raw SIP data in metadata with enhanced filtering fields
        metadatas.append({
            'type': 'sip',
            'sip_id': f'sip_{idx}',
            'is_active': is_active,
            'status': 'active' if is_active else 'inactive',
            'frequency': frequency.lower(),
            'scheme_name': sip.get('scheme_name', ''),
            'broker': sip.get('broker', 'Direct'),
            'data': json.dumps(sip, default=json_serial)  # Complete unprocessed data
        })
    
    # 4. INDEX BROKER INFORMATION (raw data)
    broker_info = portfolio_data.get('broker_info', {})
    for broker_name, broker_data in broker_info.items():
        text = (
            f"Broker: {broker_name} - "
            f"{broker_data.get('scheme_count', 0)} schemes, "
            f"₹{broker_data.get('total_invested', 0):,.0f} total invested, "
            f"{broker_data.get('transaction_count', 0)} transactions"
        )
        
        texts.append(text)
        metadatas.append({
            'type': 'broker',
            'broker_name': broker_name,
            'data': json.dumps(broker_data, default=json_serial)
        })
    
    # 5. INDEX AGGREGATION MAP (for understanding duplicate funds)
    aggregation_map = portfolio_data.get('aggregation_map', {})
    if aggregation_map:
        for scheme_key, agg_info in aggregation_map.items():
            text = (
                f"Aggregated fund: {agg_info.get('display_scheme_name', 'Unknown')} - "
                f"{agg_info.get('original_count', 0)} folios merged: "
                f"{', '.join(agg_info.get('folios', []))}"
            )
            
            texts.append(text)
            metadatas.append({
                'type': 'aggregation',
                'scheme_key': scheme_key,
                'data': json.dumps(agg_info, default=json_serial)
            })
    
    # Index in FAISS
    if texts:
        store.add_texts(texts, metadatas)
        print(f"✓ Indexed {len(texts)} items in FAISS for RAG")
        print(f"  - 1 portfolio summary")
        print(f"  - {len(portfolio_data.get('holdings', []))} holdings")
        print(f"  - {len(portfolio_data.get('active_sips', []))} SIPs")
        print(f"  - {len(broker_info)} brokers")
        print(f"  - {len(aggregation_map)} aggregated funds")


# For backward compatibility
def index_portfolio(portfolio_data: Dict):
    """Alias for index_portfolio_data"""
    return index_portfolio_data(portfolio_data)

"""
Portfolio Indexer for FAISS
Indexes portfolio holdings for semantic search
"""
from vector_db.faiss_store import LocalVectorStore
from typing import Dict, List

def index_portfolio_data(portfolio_data: Dict):
    """
    Index portfolio holdings in FAISS
    
    Args:
        portfolio_data: Portfolio dictionary with holdings
    """
    store = LocalVectorStore()
    
    # Clear existing data
    store.clear()
    
    texts = []
    metadatas = []
    
    # Index each holding
    for holding in portfolio_data.get('holdings', []):
        # Create searchable text
        text = f"{holding['scheme_name']} - {holding.get('amc', '')} - "
        text += f"Type: {holding.get('type', 'EQUITY')} - "
        text += f"Current Value: ₹{holding.get('current_value', 0):,.0f} - "
        text += f"Units: {holding.get('units', 0):.2f} - "
        text += f"NAV: ₹{holding.get('current_nav', 0):.2f}"
        
        texts.append(text)
        metadatas.append({
            'type': 'holding',
            'scheme_name': holding['scheme_name'],
            'folio': holding.get('folio_number', ''),
            'fund_type': holding.get('type', 'EQUITY'),
            'isin': holding.get('isin', '')
        })
    
    # Add portfolio summary
    summary_text = f"Total portfolio value: ₹{portfolio_data.get('total_value', 0):,.0f}, "
    summary_text += f"Total invested: ₹{portfolio_data.get('total_invested', 0):,.0f}, "
    summary_text += f"Total gain: ₹{portfolio_data.get('total_gain', 0):,.0f}, "
    summary_text += f"XIRR: {portfolio_data.get('xirr', 0):.2f}%"
    
    texts.append(summary_text)
    metadatas.append({
        'type': 'summary',
        'investor': portfolio_data.get('investor_name', '')
    })
    
    # Add allocation info
    allocation = portfolio_data.get('allocation', {})
    alloc_text = f"Asset allocation - Equity: {allocation.get('equity', 0):.1f}%, "
    alloc_text += f"Debt: {allocation.get('debt', 0):.1f}%, "
    alloc_text += f"Hybrid: {allocation.get('hybrid', 0):.1f}%"
    
    texts.append(alloc_text)
    metadatas.append({
        'type': 'allocation'
    })
    
    # Index in FAISS
    if texts:
        store.add_texts(texts, metadatas)
        print(f"✓ Indexed {len(texts)} items in FAISS")


# For backward compatibility
def index_portfolio(portfolio_data: Dict):
    """Alias for index_portfolio_data"""
    return index_portfolio_data(portfolio_data)

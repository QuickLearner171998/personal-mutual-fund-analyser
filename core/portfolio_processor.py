"""
Core business logic for MF Portfolio processing
Shared between main.py (testing) and app.py (Streamlit UI)
"""
import json
from pathlib import Path
from typing import Dict, Tuple, Optional
from cas_import.mf_central_parser import MFCentralParser
from database.json_store import PortfolioStore
from vector_db.portfolio_indexer import index_portfolio_data


def load_mf_central_files(
    consolidated_path: Path,
    transaction_path: Path,
    detailed_path: Path
) -> Tuple[Dict, Dict, list]:
    """
    Load and validate MF Central JSON files
    
    Returns:
        Tuple of (consolidated_data, transaction_data, detailed_data)
    """
    with open(consolidated_path, 'r') as f:
        consolidated_data = json.load(f)
    
    with open(transaction_path, 'r') as f:
        transaction_data = json.load(f)
    
    with open(detailed_path, 'r') as f:
        detailed_data = json.load(f)
    
    return consolidated_data, transaction_data, detailed_data


def validate_mf_central_data(
    consolidated_data: Dict,
    transaction_data: Dict,
    detailed_data: list
) -> Tuple[bool, Optional[str]]:
    """
    Validate MF Central JSON structure
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check consolidated data
        if 'dtTrxnResult' not in consolidated_data:
            return False, 'Consolidated file missing dtTrxnResult'
        
        if not consolidated_data['dtTrxnResult']:
            return False, 'Consolidated file has no holdings'
        
        # Check transaction data
        if 'dtTrxnResult' not in transaction_data:
            return False, 'Transaction file missing dtTrxnResult'
        
        # Check detailed data
        if not isinstance(detailed_data, list):
            return False, 'Detailed report should be a list'
        
        if not detailed_data:
            return False, 'Detailed report is empty'
        
        # Check required fields in first entry
        required_consolidated_fields = ['Scheme', 'Folio', 'Unit Balance', 'Current Value(Rs.)']
        first_holding = consolidated_data['dtTrxnResult'][0]
        
        for field in required_consolidated_fields:
            if field not in first_holding:
                return False, f'Missing field in consolidated data: {field}'
        
        # Check detailed report fields
        required_detailed_fields = ['Scheme', 'Folio', 'CurrentValue', 'Annualised XIRR']
        first_detailed = detailed_data[0]
        
        for field in required_detailed_fields:
            if field not in first_detailed:
                return False, f'Missing field in detailed report: {field}'
        
        return True, None
        
    except Exception as e:
        return False, str(e)


def process_mf_central_data(
    consolidated_data: Dict = None,
    transaction_data: Dict = None,
    detailed_data: list = None,
    excel_path: str = None,
    save_to_db: bool = True,
    index_for_qa: bool = True
) -> Tuple[Dict, list]:
    """
    Parse MF Central data and optionally save/index
    
    Supports two modes:
    1. Excel mode: excel_path + transaction_data (NEW, RECOMMENDED)
    2. JSON mode: consolidated_data + transaction_data + detailed_data (LEGACY)
    
    Args:
        excel_path: Path to Excel file (if using Excel mode)
        transaction_data: Transaction details JSON
        consolidated_data: Consolidated portfolio JSON (legacy)
        detailed_data: Detailed report JSON (legacy)
        save_to_db: Whether to save to database
        index_for_qa: Whether to index for Q&A
    
    Returns:
        Tuple of (portfolio_data, transactions)
    """
    
    if excel_path:
        # NEW: Excel + JSON mode
        from core.unified_processor import process_mf_central_complete
        import tempfile
        import json
        
        # Save transaction data to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(transaction_data, f)
            txn_path = f.name
        
        try:
            portfolio_data = process_mf_central_complete(excel_path, txn_path)
            transactions = []  # Not returned in new mode
        finally:
            import os
            os.unlink(txn_path)
    
    else:
        # LEGACY: JSON-only mode
        from cas_import.mf_central_parser import MFCentralParser
        
        parser = MFCentralParser()
        portfolio_data = parser.build_portfolio_data(
            consolidated_data,
            transaction_data,
            detailed_data
        )
        transactions = parser.transaction_data
    
    # Save to database
    if save_to_db:
        from database.json_store import PortfolioStore
        store = PortfolioStore()
        store.save_complete_data(
            portfolio=portfolio_data,
            transactions=[],
            sips=portfolio_data.get('active_sips', []),
            broker_info=portfolio_data.get('broker_info', {}),
            aggregation_map=portfolio_data.get('aggregation_map', {})
        )
    
    # Index for Q&A
    if index_for_qa:
        try:
            from vector_db.portfolio_indexer import index_portfolio_data
            index_portfolio_data(portfolio_data)
        except Exception as e:
            print(f"⚠️  Vector indexing skipped: {str(e)}")
    
    return portfolio_data, transactions


def get_portfolio_summary(portfolio_data: Dict) -> Dict:
    """
    Extract key portfolio metrics for display
    
    Returns:
        Dict with summary metrics
    """
    return {
        'investor_name': portfolio_data.get('investor_name', ''),
        'pan': portfolio_data.get('pan', ''),
        'total_value': portfolio_data.get('total_value', 0),
        'total_invested': portfolio_data.get('total_invested', 0),
        'total_gain': portfolio_data.get('total_gain', 0),
        'total_gain_percent': portfolio_data.get('total_gain_percent', 0),
        'xirr': portfolio_data.get('xirr', 0),
        'num_funds': portfolio_data.get('num_funds', 0),
        'num_aggregated_funds': portfolio_data.get('num_aggregated_funds', 0),
        'num_active_sips': portfolio_data.get('num_active_sips', 0),
        'num_brokers': portfolio_data.get('num_brokers', 0),
        'data_source': portfolio_data.get('data_source', 'Unknown')
    }


def get_transaction_summary(transactions: list) -> Dict:
    """
    Summarize transactions by type
    
    Returns:
        Dict with transaction counts by type
    """
    summary = {
        'total': len(transactions),
        'by_type': {}
    }
    
    for txn in transactions:
        txn_type = txn.get('transaction_type', 'unknown')
        summary['by_type'][txn_type] = summary['by_type'].get(txn_type, 0) + 1
    
    return summary


def load_portfolio_from_db() -> Optional[Dict]:
    """
    Load portfolio from database
    
    Returns:
        Portfolio data or None if not found
    """
    store = PortfolioStore()
    return store.get_portfolio()


def check_sample_files_exist() -> Tuple[bool, list]:
    """
    Check if sample MF Central files exist
    
    Returns:
        Tuple of (all_exist, missing_files)
    """
    base_dir = Path(__file__).parent.parent
    
    files = {
        'consolidated': base_dir / "CCJN4KTLB310840997771IMBAS199068013/CurrentValuationAS199068013.json",
        'transaction': base_dir / "CCJN4KTLB310840997771IMBAS199068013/AS199068013.json",
        'detailed': base_dir / "70910727520211641ZF683740997FF11IMBPF199067986.json"
    }
    
    missing = [name for name, path in files.items() if not path.exists()]
    
    return len(missing) == 0, missing

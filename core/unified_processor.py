"""
Unified MF Central Data Processor
Combines Excel (holdings) + JSON (transactions/SIPs) for complete portfolio view
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Dict, List, Tuple
from cas_import.excel_parser import parse_mf_central_excel
from cas_import.mf_central_parser import MFCentralParser


def process_mf_central_complete(
    excel_path: str,
    transaction_json_path: str,
    xirr_json_path: str = None,
    consolidated_json_path: str = None
) -> Dict:
    """
    Process MF Central data using:
    - Excel: Primary source for current holdings (most up-to-date)
    - Transaction JSON: For SIP detection and broker info
    - XIRR JSON: For fund-wise XIRR data (REQUIRED for accurate XIRR)
    - Consolidated JSON: Optional, for additional validation
    
    Args:
        excel_path: Path to Excel detailed report
        transaction_json_path: Path to transaction JSON
        xirr_json_path: Path to XIRR JSON (detailed report)
        consolidated_json_path: Optional path to consolidated JSON
        
    Returns:
        Complete portfolio data
    """
    import json
    
    # 1. Parse Excel for holdings (primary source)
    print("📊 Parsing Excel for holdings...")
    excel_data = parse_mf_central_excel(excel_path)
    holdings = excel_data['holdings']
    
    # 2. Parse transaction JSON
    print("📝 Parsing transaction JSON...")
    with open(transaction_json_path, 'r') as f:
        transaction_json = json.load(f)
    
    parser = MFCentralParser()
    transactions = parser.parse_transaction_details(transaction_json)
    
    # 3. Identify active SIPs from transactions
    print("🔍 Identifying active SIPs...")
    active_sips = parser.identify_active_sips(transactions)
    
    # 4. Extract broker information
    print("🤝 Extracting broker information...")
    broker_info = parser.extract_broker_info(transactions)
    
    # 5. Parse XIRR JSON if provided
    xirr_map = {}
    if xirr_json_path:
        print("📈 Parsing XIRR data...")
        with open(xirr_json_path, 'r') as f:
            xirr_json = json.load(f)
        
        # Create XIRR lookup map (scheme + folio -> XIRR)
        for item in xirr_json:
            key = (item.get('Scheme', ''), item.get('Folio', ''))
            xirr_map[key] = float(item.get('Annualised XIRR', 0))
    
    # 6. Enrich holdings with XIRR
    print("🔗 Enriching holdings with XIRR...")
    holdings = _enrich_holdings_with_xirr(holdings, xirr_map)
    
    # 7. Enrich holdings with broker info from transactions
    print("🔗 Enriching holdings with broker data...")
    holdings = _enrich_holdings_with_broker(holdings, transactions)
    
    # 8. Calculate portfolio XIRR
    portfolio_xirr = _calculate_portfolio_xirr(holdings)
    
    # 9. Get investor info from transactions
    investor_name = transactions[0]['investor_name'] if transactions else ''
    pan = transactions[0]['pan'] if transactions else ''
    
    # 10. Build final portfolio data
    portfolio_data = {
        'investor_name': investor_name,
        'pan': pan,
        'total_value': excel_data['total_value'],
        'total_invested': excel_data['total_invested'],
        'total_gain': excel_data['total_gain'],
        'total_gain_percent': excel_data['total_gain_percent'],
        'xirr': portfolio_xirr,  # Will be calculated if needed
        'holdings': holdings,
        'active_sips': active_sips,
        'broker_info': broker_info,
        'num_funds': excel_data['num_funds'],
        'num_active_sips': len(active_sips),
        'num_brokers': len(broker_info),
        'data_source': 'MF Central (Excel + JSON)',
        'last_updated': excel_data.get('last_updated', '')
    }
    
    return portfolio_data


def _enrich_holdings_with_broker(holdings: List[Dict], transactions: List[Dict]) -> List[Dict]:
    """Add broker information to holdings from transaction history"""
    
    # Build broker map from transactions (scheme + folio -> broker)
    broker_map = {}
    for txn in transactions:
        if txn.get('broker') and txn['broker'] != 'Unknown':
            key = (txn['scheme_name'], txn['folio_number'])
            if key not in broker_map:
                broker_map[key] = txn['broker']
    
    # Enrich holdings
    for holding in holdings:
        # Try exact match first
        key = (holding['scheme_name'], holding['folio_number'])
        if key in broker_map:
            holding['broker'] = broker_map[key]
        else:
            # Try fuzzy match on scheme name
            for (txn_scheme, txn_folio), broker in broker_map.items():
                if (txn_folio == holding['folio_number'] and 
                    _schemes_match(txn_scheme, holding['scheme_name'])):
                    holding['broker'] = broker
                    break
            else:
                holding['broker'] = 'Unknown'
    
    return holdings


def _schemes_match(scheme1: str, scheme2: str) -> bool:
    """Check if two scheme names refer to the same fund"""
    # Normalize and compare
    s1 = scheme1.lower().replace('-', '').replace(' ', '')
    s2 = scheme2.lower().replace('-', '').replace(' ', '')
    
    # Check if one contains the other (handles truncation)
    return s1 in s2 or s2 in s1 or s1[:30] == s2[:30]


def _enrich_holdings_with_xirr(holdings: List[Dict], xirr_map: Dict) -> List[Dict]:
    """Add XIRR data to holdings from XIRR JSON"""
    
    for holding in holdings:
        # Try exact match first
        key = (holding['scheme_name'], holding['folio_number'])
        if key in xirr_map:
            holding['xirr'] = xirr_map[key]
        else:
            # Try fuzzy match on scheme name
            for (xirr_scheme, xirr_folio), xirr_value in xirr_map.items():
                if (xirr_folio == holding['folio_number'] and 
                    _schemes_match(xirr_scheme, holding['scheme_name'])):
                    holding['xirr'] = xirr_value
                    break
            else:
                holding['xirr'] = 0.0
    
    return holdings


def _calculate_portfolio_xirr(holdings: List[Dict]) -> float:
    """Calculate weighted average XIRR for portfolio"""
    if not holdings:
        return 0.0
    
    total_value = sum(h.get('current_value', 0) for h in holdings)
    if total_value == 0:
        return 0.0
    
    weighted_xirr = sum(
        h.get('xirr', 0) * h.get('current_value', 0)
        for h in holdings
    ) / total_value
    
    return round(weighted_xirr, 2)


if __name__ == "__main__":
    # Test
    portfolio = process_mf_central_complete(
        'cas_detailed_report_2025_11_26_004753.xlsx',
        'CCJN4KTLB310840997771IMBAS199068013/AS199068013.json',
        '70910727520211641ZF683740997FF11IMBPF199067986.json'
    )
    
    print(f"\n{'='*80}")
    print("PORTFOLIO SUMMARY")
    print(f"{'='*80}")
    print(f"Investor: {portfolio['investor_name']}")
    print(f"Total Value: ₹{portfolio['total_value']:,.2f}")
    print(f"Total Invested: ₹{portfolio['total_invested']:,.2f}")
    print(f"Total Gain: ₹{portfolio['total_gain']:,.2f} ({portfolio['total_gain_percent']:.2f}%)")
    print(f"\nHoldings: {portfolio['num_funds']}")
    print(f"Active SIPs: {portfolio['num_active_sips']}")
    print(f"Brokers: {portfolio['num_brokers']}")
    
    print(f"\n{'='*80}")
    print("ACTIVE SIPs")
    print(f"{'='*80}")
    for sip in portfolio['active_sips'][:10]:
        print(f"{sip['scheme_name'][:50]:50s} | ₹{sip['sip_amount']:>10,.2f} | {sip['frequency']:10s} | {sip['broker']}")

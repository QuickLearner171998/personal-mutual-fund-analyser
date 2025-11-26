"""
Unified MF Central Data Processor
Combines Excel (holdings) + JSON (transactions/SIPs) for complete portfolio view
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Dict, List, Tuple
from collections import defaultdict
import re
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


def extract_base_folio(folio: str) -> str:
    """
    Extract base folio number from folio string.
    Handles suffixes like '20920295/55' -> '20920295'
    """
    if not folio:
        return ''
    
    # Remove suffix after '/'
    base = str(folio).split('/')[0].strip()
    return base


def _enrich_holdings_with_broker(holdings: List[Dict], transactions: List[Dict]) -> List[Dict]:
    """
    Add broker information to holdings from transaction history.
    Matches using folio number (with base folio extraction).
    """
    
    # Build broker map from transactions (base_folio -> broker)
    # Use base folio as key to handle folio suffixes
    broker_map = {}
    for txn in transactions:
        if txn.get('broker') and txn['broker'] != 'Unknown':
            base_folio = extract_base_folio(txn['folio_number'])
            if base_folio and base_folio not in broker_map:
                broker_map[base_folio] = txn['broker']
    
    # Enrich holdings
    for holding in holdings:
        base_folio = extract_base_folio(holding['folio_number'])
        
        # Try base folio match
        if base_folio in broker_map:
            holding['broker'] = broker_map[base_folio]
        else:
            # Try fuzzy match on scheme name as fallback
            for txn in transactions:
                if txn.get('broker') and txn['broker'] != 'Unknown':
                    if _schemes_match(txn['scheme_name'], holding['scheme_name']):
                        holding['broker'] = txn['broker']
                        break
            else:
                # Don't set broker if not found
                if 'broker' not in holding:
                    holding['broker'] = None
    
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


def _normalize_scheme_for_grouping(scheme_name: str) -> str:
    """
    Normalize scheme name for grouping duplicate funds.
    Uses similar logic as MFCentralParser but more aggressive.
    """
    normalized = scheme_name.lower()
    
    # Remove plan type variations
    normalized = re.sub(r'\s*-?\s*(regular|direct)\s*plan\s*-?\s*', ' ', normalized)
    normalized = re.sub(r'\s*-?\s*(regular|direct)\s*-?\s*', ' ', normalized)
    
    # Remove growth variations
    normalized = re.sub(r'\s*-\s*growth\s*plan\s*', ' ', normalized)
    normalized = re.sub(r'\s*-\s*growth\s*', ' ', normalized)
    normalized = re.sub(r'\bgrowth\b', '', normalized)
    
    # Remove parenthetical text
    normalized = re.sub(r'\s*\(.*?\)\s*', ' ', normalized)
    
    # Remove "formerly known as"
    normalized = re.sub(r'\s*formerly\s+known\s+as\s+.*$', '', normalized)
    
    # Normalize abbreviations
    normalized = re.sub(r'\bfund\s*-?\s*', '', normalized)
    normalized = re.sub(r'\breg\s+pl\b', '', normalized)
    normalized = re.sub(r'\breg\b', '', normalized)
    normalized = re.sub(r'\bdp\b', '', normalized)
    
    # Clean up
    normalized = re.sub(r'\s*-\s*', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def aggregate_holdings_for_display(holdings: List[Dict]) -> Tuple[List[Dict], Dict]:
    """
    Aggregate holdings by normalized scheme name for display.
    Returns: (aggregated_holdings, aggregation_map)
    
    Each aggregated holding has:
    - All aggregated financial values (summed)
    - Weighted average XIRR
    - List of individual folio details for expansion
    - Flag indicating if it's aggregated
    """
    # Group by normalized scheme name
    scheme_groups = defaultdict(list)
    
    for holding in holdings:
        normalized_name = _normalize_scheme_for_grouping(holding['scheme_name'])
        scheme_groups[normalized_name].append(holding)
    
    aggregated_holdings = []
    aggregation_map = {}
    
    for normalized_name, group in scheme_groups.items():
        if len(group) == 1:
            # No aggregation needed
            holding = group[0].copy()
            holding['is_aggregated'] = False
            holding['folio_count'] = 1
            holding['individual_folios'] = []
            aggregated_holdings.append(holding)
        else:
            # Aggregate multiple folios
            aggregated = _aggregate_holdings_group(group)
            aggregated['is_aggregated'] = True
            aggregated['folio_count'] = len(group)
            aggregated['individual_folios'] = group
            aggregated_holdings.append(aggregated)
            
            # Store aggregation info
            aggregation_map[normalized_name] = {
                'original_count': len(group),
                'folios': [h['folio_number'] for h in group],
                'display_scheme_name': group[0]['scheme_name']
            }
    
    return aggregated_holdings, aggregation_map


def _aggregate_holdings_group(group: List[Dict]) -> Dict:
    """
    Aggregate a group of holdings into one summary.
    Calculates weighted average XIRR based on current values.
    """
    # Start with first holding as template
    aggregated = group[0].copy()
    
    # Sum numerical fields
    aggregated['units'] = sum(h.get('units', 0) for h in group)
    aggregated['current_value'] = sum(h.get('current_value', 0) for h in group)
    aggregated['cost_value'] = sum(h.get('cost_value', 0) for h in group)
    aggregated['gain_loss'] = aggregated['current_value'] - aggregated['cost_value']
    
    # Recalculate percentages
    aggregated['gain_loss_percent'] = (
        (aggregated['gain_loss'] / aggregated['cost_value'] * 100)
        if aggregated['cost_value'] > 0 else 0
    )
    
    # Calculate weighted average XIRR
    total_value = aggregated['current_value']
    if total_value > 0:
        weighted_xirr = sum(
            h.get('xirr', 0) * h.get('current_value', 0)
            for h in group
        ) / total_value
        aggregated['xirr'] = round(weighted_xirr, 2)
    else:
        aggregated['xirr'] = 0.0
    
    # Recalculate current NAV
    aggregated['current_nav'] = (
        aggregated['current_value'] / aggregated['units']
        if aggregated['units'] > 0 else 0
    )
    
    # Use most recent NAV date
    nav_dates = [h.get('nav_date') for h in group if h.get('nav_date')]
    if nav_dates:
        aggregated['nav_date'] = max(nav_dates)
    
    # Create combined folio display
    folios = [h['folio_number'] for h in group]
    aggregated['folio_number'] = f"{folios[0]} (+{len(folios)-1} more)"
    
    return aggregated


def match_sips_with_holdings(sips: List[Dict], holdings: List[Dict]) -> List[Dict]:
    """
    Match SIP data with holdings to add performance metrics.
    Returns enriched SIP list with XIRR, returns, and current value.
    """
    # Build holding lookup map (base_folio + normalized_scheme -> holding)
    holding_map = {}
    for holding in holdings:
        base_folio = extract_base_folio(holding['folio_number'])
        normalized_scheme = _normalize_scheme_for_grouping(holding['scheme_name'])
        key = (base_folio, normalized_scheme)
        holding_map[key] = holding
    
    enriched_sips = []
    for sip in sips.copy():
        base_folio = extract_base_folio(sip['folio_number'])
        normalized_scheme = _normalize_scheme_for_grouping(sip['scheme_name'])
        key = (base_folio, normalized_scheme)
        
        # Try to find matching holding
        holding = holding_map.get(key)
        
        if holding:
            # Add performance metrics from holding
            sip['xirr'] = holding.get('xirr', 0.0)
            sip['current_value'] = holding.get('current_value', 0.0)
            sip['total_invested_sip'] = sip.get('total_invested', 0.0)
            sip['absolute_returns'] = sip['current_value'] - sip['total_invested_sip']
            sip['returns_percent'] = (
                (sip['absolute_returns'] / sip['total_invested_sip'] * 100)
                if sip['total_invested_sip'] > 0 else 0.0
            )
        else:
            # No matching holding found (SIP might be redeemed)
            sip['xirr'] = 0.0
            sip['current_value'] = 0.0
            sip['total_invested_sip'] = sip.get('total_invested', 0.0)
            sip['absolute_returns'] = 0.0
            sip['returns_percent'] = 0.0
        
        enriched_sips.append(sip)
    
    return enriched_sips


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

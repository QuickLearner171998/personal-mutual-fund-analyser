"""
MF Central Data Parser
Parses JSON files from MF Central:
1. CONSOLIDATED PORTFOLIO STATEMENT (CurrentValuation*.json)
2. TRANSACTION DETAILS STATEMENT (AS*.json)
3. MF Central Detailed Report (*.json with XIRR data)
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
from collections import defaultdict
import re


class MFCentralParser:
    """Parser for MF Central JSON data sources"""
    
    def __init__(self):
        self.consolidated_data = None
        self.transaction_data = None
        self.detailed_report_data = None
        
    def parse_consolidated_portfolio(self, json_data: Dict) -> List[Dict]:
        """
        Parse CONSOLIDATED PORTFOLIO STATEMENT JSON
        Returns list of current holdings with valuation
        """
        holdings = []
        
        if 'dtTrxnResult' in json_data:
            for item in json_data['dtTrxnResult']:
                # Skip entries with zero units
                if item.get('Unit Balance', 0) == 0:
                    continue
                    
                holding = {
                    'amc': item.get('AMC Name', ''),
                    'scheme_name': item.get('Scheme', ''),
                    'scheme_code': item.get('SCHEMECODE', ''),
                    'type': item.get('Type', ''),
                    'folio_number': item.get('Folio', ''),
                    'investor_name': item.get('Investor Name', ''),
                    'pan': item.get('PAN', ''),
                    'units': float(item.get('Unit Balance', 0)),
                    'nav_date': self._parse_date(item.get('NAV Date')),
                    'current_value': float(item.get('Current Value(Rs.)', 0)),
                    'cost_value': float(item.get('Cost Value(Rs.)', 0)),
                }
                
                # Calculate gain/loss
                holding['gain_loss'] = holding['current_value'] - holding['cost_value']
                holding['gain_loss_percent'] = (
                    (holding['gain_loss'] / holding['cost_value'] * 100) 
                    if holding['cost_value'] > 0 else 0
                )
                
                # Calculate current NAV
                holding['current_nav'] = (
                    holding['current_value'] / holding['units'] 
                    if holding['units'] > 0 else 0
                )
                
                holdings.append(holding)
        
        self.consolidated_data = holdings
        return holdings
    
    def parse_transaction_details(self, json_data: Dict) -> List[Dict]:
        """
        Parse TRANSACTION DETAILS STATEMENT JSON
        Returns list of all transactions with broker info
        """
        transactions = []
        
        if 'dtTrxnResult' in json_data:
            for item in json_data['dtTrxnResult']:
                # Skip non-financial transactions
                if item.get('AMOUNT') is None and item.get('UNITS') is None:
                    continue
                
                # Parse transaction type
                txn_type = self._classify_transaction_type(item.get('TRANSACTION_TYPE', ''))
                
                # Skip if not a meaningful transaction
                if txn_type == 'other':
                    continue
                
                transaction = {
                    'mf_name': item.get('MF_NAME', ''),
                    'investor_name': item.get('INVESTOR_NAME', ''),
                    'pan': item.get('PAN', ''),
                    'folio_number': item.get('FOLIO_NUMBER', ''),
                    'product_code': item.get('PRODUCT_CODE', ''),
                    'scheme_name': item.get('SCHEME_NAME', ''),
                    'type': item.get('Type', ''),
                    'trade_date': self._parse_date(item.get('TRADE_DATE')),
                    'transaction_type': txn_type,
                    'original_transaction_type': item.get('TRANSACTION_TYPE', ''),
                    'amount': float(item.get('AMOUNT', 0) or 0),
                    'units': float(item.get('UNITS', 0) or 0),
                    'price': float(item.get('PRICE', 0) or 0),
                    'broker': self._extract_broker_name(item.get('BROKER', '')),
                    'broker_raw': item.get('BROKER', ''),
                }
                
                transactions.append(transaction)
        
        self.transaction_data = transactions
        return transactions
    
    def parse_detailed_report(self, json_data: List[Dict]) -> List[Dict]:
        """
        Parse MF Central Detailed Report JSON
        Returns list of holdings with XIRR data
        """
        holdings = []
        
        for item in json_data:
            holding = {
                'amc': item.get('AMCName', ''),
                'scheme_name': item.get('Scheme', ''),
                'type': item.get('Type', ''),
                'folio_number': item.get('Folio', ''),
                'investor_name': item.get('InvestorName', ''),
                'units': float(item.get('UnitBal', 0)),
                'nav_date': item.get('NAVDate', ''),
                'current_value': float(item.get('CurrentValue', 0)),
                'cost_value': float(item.get('CostValue', 0)),
                'appreciation': float(item.get('Appreciation', 0)),
                'weighted_avg_cost': float(item.get('WtgAvg', 0)),
                'xirr': float(item.get('Annualised XIRR', 0)),
            }
            
            holdings.append(holding)
        
        self.detailed_report_data = holdings
        return holdings
    
    def aggregate_duplicate_funds(self, holdings: List[Dict]) -> Tuple[List[Dict], Dict]:
        """
        Aggregate duplicate funds (same scheme across different folios)
        Returns: (aggregated_holdings, aggregation_map)
        """
        # Group by scheme name
        scheme_groups = defaultdict(list)
        
        for holding in holdings:
            # Normalize scheme name for grouping
            normalized_name = self._normalize_scheme_name(holding['scheme_name'])
            scheme_groups[normalized_name].append(holding)
        
        aggregated_holdings = []
        aggregation_map = {}
        
        for normalized_name, group in scheme_groups.items():
            if len(group) == 1:
                # No aggregation needed
                aggregated_holdings.append(group[0])
            else:
                # Aggregate multiple folios
                aggregated = self._aggregate_holdings_group(group)
                aggregated['aggregated_folios'] = [h['folio_number'] for h in group]
                aggregated['is_aggregated'] = True
                aggregated_holdings.append(aggregated)
                
                # Store aggregation mapping
                aggregation_map[normalized_name] = {
                    'original_count': len(group),
                    'folios': [h['folio_number'] for h in group],
                    'scheme_name': group[0]['scheme_name']
                }
        
        return aggregated_holdings, aggregation_map
    
    def identify_active_sips(self, transactions: List[Dict]) -> List[Dict]:
        """
        Identify active SIPs from transaction patterns
        Returns list of active SIP details
        """
        # Group SIP transactions by scheme and folio
        sip_groups = defaultdict(list)
        
        for txn in transactions:
            if txn['transaction_type'] == 'sip' and txn.get('trade_date'):
                key = (txn['scheme_name'], txn['folio_number'])
                sip_groups[key].append(txn)
        
        active_sips = []
        
        for (scheme_name, folio), sip_txns in sip_groups.items():
            if not sip_txns:
                continue
            
            # Filter out any with None dates
            sip_txns = [t for t in sip_txns if t.get('trade_date')]
            
            if not sip_txns:
                continue
            
            # Sort by date
            sip_txns.sort(key=lambda x: x['trade_date'])
            
            # Get last SIP transaction
            last_sip = sip_txns[-1]
            
            # Check if SIP is active (last transaction within 60 days)
            days_since_last = (date.today() - last_sip['trade_date']).days
            
            if days_since_last <= 60:  # Consider active if last SIP within 2 months
                # Calculate frequency
                frequency = self._calculate_sip_frequency(sip_txns)
                
                # Calculate next installment date
                next_date = self._calculate_next_sip_date(
                    last_sip['trade_date'], 
                    frequency
                )
                
                # Get most common SIP amount
                amounts = [txn['amount'] for txn in sip_txns]
                sip_amount = max(set(amounts), key=amounts.count)
                
                sip_detail = {
                    'scheme_name': scheme_name,
                    'folio_number': folio,
                    'sip_amount': abs(sip_amount),
                    'frequency': frequency,
                    'start_date': sip_txns[0]['trade_date'],
                    'last_installment_date': last_sip['trade_date'],
                    'next_installment_date': next_date,
                    'total_installments': len(sip_txns),
                    'is_active': True,
                    'broker': last_sip['broker'],
                    'total_invested': sum(abs(txn['amount']) for txn in sip_txns)
                }
                
                active_sips.append(sip_detail)
        
        return active_sips
    
    def extract_broker_info(self, transactions: List[Dict]) -> Dict[str, Dict]:
        """
        Extract broker information and calculate broker-wise statistics
        Returns dict mapping broker name to stats
        """
        broker_stats = defaultdict(lambda: {
            'total_invested': 0,
            'schemes': set(),
            'transaction_count': 0,
            'first_transaction': None,
            'last_transaction': None
        })
        
        for txn in transactions:
            if txn['transaction_type'] in ['purchase', 'sip']:
                broker = txn['broker']
                if not broker or broker == 'Unknown':
                    continue
                
                stats = broker_stats[broker]
                stats['total_invested'] += abs(txn['amount'])
                stats['schemes'].add(txn['scheme_name'])
                stats['transaction_count'] += 1
                
                txn_date = txn.get('trade_date')
                if txn_date:  # Only process if date exists
                    if stats['first_transaction'] is None or txn_date < stats['first_transaction']:
                        stats['first_transaction'] = txn_date
                    if stats['last_transaction'] is None or txn_date > stats['last_transaction']:
                        stats['last_transaction'] = txn_date
        
        # Convert sets to lists for JSON serialization
        for broker, stats in broker_stats.items():
            stats['schemes'] = list(stats['schemes'])
            stats['scheme_count'] = len(stats['schemes'])
        
        return dict(broker_stats)
    
    def build_portfolio_data(
        self, 
        consolidated_json: Dict,
        transaction_json: Dict,
        detailed_report_json: List[Dict]
    ) -> Dict:
        """
        Combine all data sources into unified portfolio structure
        """
        # Parse all data sources
        holdings = self.parse_consolidated_portfolio(consolidated_json)
        transactions = self.parse_transaction_details(transaction_json)
        detailed_holdings = self.parse_detailed_report(detailed_report_json)
        
        # Enrich holdings with XIRR from detailed report
        holdings = self._enrich_with_xirr(holdings, detailed_holdings)
        
        # Aggregate duplicate funds
        aggregated_holdings, aggregation_map = self.aggregate_duplicate_funds(holdings)
        
        # Identify active SIPs
        active_sips = self.identify_active_sips(transactions)
        
        # Extract broker information
        broker_info = self.extract_broker_info(transactions)
        
        # Calculate portfolio totals
        total_value = sum(h['current_value'] for h in holdings)
        total_invested = sum(h['cost_value'] for h in holdings)
        total_gain = total_value - total_invested
        
        # Calculate portfolio XIRR from detailed report
        portfolio_xirr = self._calculate_portfolio_xirr(detailed_holdings)
        
        # Get investor info
        investor_name = holdings[0]['investor_name'] if holdings else ''
        pan = holdings[0]['pan'] if holdings else ''
        
        portfolio_data = {
            'investor_name': investor_name,
            'pan': pan,
            'total_value': total_value,
            'total_invested': total_invested,
            'total_gain': total_gain,
            'total_gain_percent': (total_gain / total_invested * 100) if total_invested > 0 else 0,
            'xirr': portfolio_xirr,
            'holdings': holdings,
            'aggregated_holdings': aggregated_holdings,
            'aggregation_map': aggregation_map,
            'active_sips': active_sips,
            'broker_info': broker_info,
            'num_funds': len(holdings),
            'num_aggregated_funds': len(aggregated_holdings),
            'num_active_sips': len(active_sips),
            'num_brokers': len(broker_info),
            'last_updated': datetime.now().isoformat(),
            'data_source': 'MF Central'
        }
        
        return portfolio_data
    
    # Helper methods
    
    def _parse_date(self, date_str: str) -> date:
        """Parse date from various formats"""
        if not date_str:
            return None
        
        try:
            # Try ISO format first (2025-11-25T00:00:00)
            if 'T' in str(date_str):
                return datetime.fromisoformat(str(date_str).split('T')[0]).date()
            
            # Try DD-MMM-YYYY format (25-NOV-2025)
            if '-' in str(date_str):
                return datetime.strptime(str(date_str), '%d-%b-%Y').date()
            
            return None
        except:
            return None
    
    def _classify_transaction_type(self, txn_type_str: str) -> str:
        """Classify transaction type into standard categories"""
        txn_type_lower = txn_type_str.lower()
        
        if 'sip' in txn_type_lower or 'systematic investment' in txn_type_lower:
            return 'sip'
        elif 'purchase' in txn_type_lower:
            return 'purchase'
        elif 'redemption' in txn_type_lower:
            return 'redemption'
        elif 'switch-in' in txn_type_lower or 'switchin' in txn_type_lower:
            return 'switch_in'
        elif 'switch-out' in txn_type_lower:
            return 'switch_out'
        elif 'dividend' in txn_type_lower:
            return 'dividend'
        else:
            return 'other'
    
    def _extract_broker_name(self, broker_str: str) -> str:
        """Extract clean broker name from broker string"""
        if not broker_str:
            return 'Unknown'
        
        # Pattern: "MFD*/Intermediary : ARN-XXXXX / Name" or "Your Broker/Dealer is : Name"
        
        # Try to extract name after ARN
        arn_match = re.search(r'ARN-\d+\s*/\s*(.+?)(?:\s*$)', broker_str)
        if arn_match:
            return arn_match.group(1).strip()
        
        # Try to extract name after "is :"
        is_match = re.search(r'is\s*:\s*(.+?)(?:\s*$)', broker_str)
        if is_match:
            return is_match.group(1).strip()
        
        # Return cleaned string
        return broker_str.strip()
    
    def _normalize_scheme_name(self, scheme_name: str) -> str:
        """Normalize scheme name for grouping"""
        # Remove common suffixes and variations
        normalized = scheme_name.lower()
        normalized = re.sub(r'\s*-\s*(regular|direct)\s*-?\s*', ' ', normalized)
        normalized = re.sub(r'\s*-\s*growth\s*plan\s*', ' ', normalized)
        normalized = re.sub(r'\s*-\s*growth\s*', ' ', normalized)
        normalized = re.sub(r'\s*\(.*?\)\s*', ' ', normalized)  # Remove parentheses
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized
    
    def _aggregate_holdings_group(self, group: List[Dict]) -> Dict:
        """Aggregate a group of holdings into one"""
        aggregated = group[0].copy()
        
        # Sum numerical fields
        aggregated['units'] = sum(h['units'] for h in group)
        aggregated['current_value'] = sum(h['current_value'] for h in group)
        aggregated['cost_value'] = sum(h['cost_value'] for h in group)
        aggregated['gain_loss'] = aggregated['current_value'] - aggregated['cost_value']
        
        # Recalculate percentages
        aggregated['gain_loss_percent'] = (
            (aggregated['gain_loss'] / aggregated['cost_value'] * 100)
            if aggregated['cost_value'] > 0 else 0
        )
        
        # Recalculate current NAV
        aggregated['current_nav'] = (
            aggregated['current_value'] / aggregated['units']
            if aggregated['units'] > 0 else 0
        )
        
        # Use most recent NAV date
        nav_dates = [h['nav_date'] for h in group if h.get('nav_date')]
        if nav_dates:
            aggregated['nav_date'] = max(nav_dates)
        
        return aggregated
    
    def _calculate_sip_frequency(self, sip_txns: List[Dict]) -> str:
        """Calculate SIP frequency from transaction dates"""
        if len(sip_txns) < 2:
            return 'Monthly'  # Default
        
        # Calculate average gap between transactions
        gaps = []
        for i in range(1, len(sip_txns)):
            gap = (sip_txns[i]['trade_date'] - sip_txns[i-1]['trade_date']).days
            gaps.append(gap)
        
        avg_gap = sum(gaps) / len(gaps)
        
        if avg_gap < 20:
            return 'Weekly'
        elif avg_gap < 60:
            return 'Monthly'
        elif avg_gap < 120:
            return 'Quarterly'
        else:
            return 'Yearly'
    
    def _calculate_next_sip_date(self, last_date: date, frequency: str) -> date:
        """Calculate next SIP installment date"""
        if frequency == 'Weekly':
            return last_date + timedelta(days=7)
        elif frequency == 'Monthly':
            # Add approximately 1 month
            next_month = last_date.month + 1
            next_year = last_date.year
            if next_month > 12:
                next_month = 1
                next_year += 1
            try:
                return date(next_year, next_month, last_date.day)
            except ValueError:
                # Handle day overflow (e.g., Jan 31 -> Feb 28)
                return date(next_year, next_month, 28)
        elif frequency == 'Quarterly':
            return last_date + timedelta(days=90)
        else:  # Yearly
            return date(last_date.year + 1, last_date.month, last_date.day)
    
    def _enrich_with_xirr(self, holdings: List[Dict], detailed_holdings: List[Dict]) -> List[Dict]:
        """Enrich holdings with XIRR data from detailed report"""
        # Create lookup map
        xirr_map = {}
        for dh in detailed_holdings:
            key = (dh['scheme_name'], dh['folio_number'])
            xirr_map[key] = dh['xirr']
        
        # Enrich holdings
        for holding in holdings:
            key = (holding['scheme_name'], holding['folio_number'])
            if key in xirr_map:
                holding['xirr'] = xirr_map[key]
            else:
                holding['xirr'] = 0.0
        
        return holdings
    
    def _calculate_portfolio_xirr(self, detailed_holdings: List[Dict]) -> float:
        """Calculate weighted average XIRR for portfolio"""
        if not detailed_holdings:
            return 0.0
        
        total_value = sum(h['current_value'] for h in detailed_holdings)
        if total_value == 0:
            return 0.0
        
        weighted_xirr = sum(
            h['xirr'] * h['current_value'] 
            for h in detailed_holdings
        ) / total_value
        
        return round(weighted_xirr, 2)


# Convenience function
def parse_mf_central_files(
    consolidated_path: str,
    transaction_path: str,
    detailed_report_path: str
) -> Dict:
    """
    Parse MF Central files and return unified portfolio data
    
    Args:
        consolidated_path: Path to CurrentValuation*.json
        transaction_path: Path to AS*.json (transaction details)
        detailed_report_path: Path to detailed report JSON with XIRR
    
    Returns:
        Complete portfolio data dictionary
    """
    parser = MFCentralParser()
    
    # Load JSON files
    with open(consolidated_path, 'r') as f:
        consolidated_json = json.load(f)
    
    with open(transaction_path, 'r') as f:
        transaction_json = json.load(f)
    
    with open(detailed_report_path, 'r') as f:
        detailed_report_json = json.load(f)
    
    # Build portfolio data
    portfolio_data = parser.build_portfolio_data(
        consolidated_json,
        transaction_json,
        detailed_report_json
    )
    
    return portfolio_data

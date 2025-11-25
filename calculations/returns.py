"""
Enhanced financial calculations for MF Central data
"""
import pyxirr
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
import pandas as pd


def calculate_cagr(initial_value: float, final_value: float, years: float) -> float:
    """
    Calculate CAGR (Compound Annual Growth Rate)
    
    Args:
        initial_value: Initial investment
        final_value: Current value
        years: Number of years
        
    Returns:
        CAGR as percentage
    """
    if initial_value <= 0 or years <= 0:
        return 0.0
    
    cagr = (pow(final_value / initial_value, 1 / years) - 1) * 100
    return round(cagr, 2)



def calculate_fund_xirr(transactions: List[Dict], current_value: float, scheme_name: str, folio: str) -> float:
    """
    Calculate XIRR for a specific fund
    
    Args:
        transactions: All transactions
        current_value: Current value of the fund
        scheme_name: Fund scheme name
        folio: Folio number
        
    Returns:
        XIRR as percentage
    """
    try:
        # Filter transactions for this fund
        fund_txns = [
            t for t in transactions 
            if t.get('scheme_name') == scheme_name and t.get('folio_number') == folio
        ]
        
        if not fund_txns:
            return 0.0
        
        dates = []
        cash_flows = []
        
        for txn in fund_txns:
            txn_date = txn['trade_date']
            if isinstance(txn_date, str):
                txn_date = datetime.strptime(txn_date, '%Y-%m-%d').date()
            
            dates.append(txn_date)
            
            # Purchases/SIPs are negative cash flows
            if txn['transaction_type'] in ['purchase', 'sip', 'switch_in']:
                cash_flows.append(-abs(txn['amount']))
            # Redemptions are positive cash flows
            elif txn['transaction_type'] in ['redemption', 'switch_out']:
                cash_flows.append(abs(txn['amount']))
        
        # Add current value as final positive cash flow
        if current_value > 0:
            dates.append(date.today())
            cash_flows.append(current_value)
        
        if len(dates) > 1:
            xirr_value = pyxirr.xirr(dates, cash_flows)
            if xirr_value is None:
                return 0.0
            return round(xirr_value * 100, 2)
        
        return 0.0
        
    except Exception as e:
        print(f"Error calculating fund XIRR for {scheme_name}: {str(e)}")
        return 0.0


def calculate_period_cagr(
    transactions: List[Dict], 
    current_value: float,
    scheme_name: str,
    folio: str,
    years: float
) -> Optional[float]:
    """
    Calculate CAGR for a specific period (1Y, 3Y, 5Y)
    
    Args:
        transactions: All transactions
        current_value: Current value
        scheme_name: Fund name
        folio: Folio number
        years: Period in years (1, 3, or 5)
        
    Returns:
        CAGR percentage or None if insufficient data
    """
    try:
        # Filter transactions for this fund
        fund_txns = [
            t for t in transactions 
            if t.get('scheme_name') == scheme_name 
            and t.get('folio_number') == folio
            and t['transaction_type'] in ['purchase', 'sip', 'switch_in']
        ]
        
        if not fund_txns:
            return None
        
        # Find transactions within the period
        cutoff_date = date.today() - timedelta(days=int(years * 365.25))
        
        # Get transactions before cutoff
        old_txns = [t for t in fund_txns if t['trade_date'] < cutoff_date]
        
        if not old_txns:
            return None  # Fund not held for this period
        
        # Calculate invested amount up to cutoff date
        initial_value = sum(abs(t['amount']) for t in old_txns)
        
        if initial_value <= 0:
            return None
        
        # Calculate CAGR
        cagr = (pow(current_value / initial_value, 1 / years) - 1) * 100
        return round(cagr, 2)
        
    except Exception as e:
        print(f"Error calculating {years}Y CAGR for {scheme_name}: {str(e)}")
        return None


def calculate_sip_returns(sip_transactions: List[Dict], current_value: float) -> Dict:
    """
    Calculate returns specifically for SIP investments
    
    Args:
        sip_transactions: List of SIP transactions for a fund
        current_value: Current value of SIP units
        
    Returns:
        Dict with SIP-specific metrics
    """
    if not sip_transactions:
        return {}
    
    try:
        total_invested = sum(abs(t['amount']) for t in sip_transactions)
        absolute_return = current_value - total_invested
        absolute_return_pct = (absolute_return / total_invested * 100) if total_invested > 0 else 0
        
        # Calculate SIP XIRR
        dates = [t['trade_date'] for t in sip_transactions]
        cash_flows = [-abs(t['amount']) for t in sip_transactions]
        
        # Add current value
        dates.append(date.today())
        cash_flows.append(current_value)
        
        xirr = 0.0
        if len(dates) > 1:
            xirr_value = pyxirr.xirr(dates, cash_flows)
            if xirr_value is not None:
                xirr = round(xirr_value * 100, 2)
        
        # Calculate average purchase NAV
        total_units = sum(t['units'] for t in sip_transactions)
        avg_nav = total_invested / total_units if total_units > 0 else 0
        
        # Current NAV
        current_nav = current_value / total_units if total_units > 0 else 0
        
        return {
            'total_invested': total_invested,
            'current_value': current_value,
            'absolute_return': absolute_return,
            'absolute_return_pct': round(absolute_return_pct, 2),
            'xirr': xirr,
            'total_installments': len(sip_transactions),
            'avg_purchase_nav': round(avg_nav, 2),
            'current_nav': round(current_nav, 2),
            'nav_appreciation': round(((current_nav - avg_nav) / avg_nav * 100), 2) if avg_nav > 0 else 0
        }
        
    except Exception as e:
        print(f"Error calculating SIP returns: {str(e)}")
        return {}


def calculate_weighted_average_cost(transactions: List[Dict]) -> float:
    """
    Calculate weighted average cost (NAV) for a fund
    
    Args:
        transactions: Purchase/SIP transactions
        
    Returns:
        Weighted average NAV
    """
    try:
        purchase_txns = [
            t for t in transactions 
            if t['transaction_type'] in ['purchase', 'sip', 'switch_in']
            and t.get('units', 0) > 0
        ]
        
        if not purchase_txns:
            return 0.0
        
        total_amount = sum(abs(t['amount']) for t in purchase_txns)
        total_units = sum(t['units'] for t in purchase_txns)
        
        if total_units <= 0:
            return 0.0
        
        return round(total_amount / total_units, 2)
        
    except Exception as e:
        print(f"Error calculating weighted average cost: {str(e)}")
        return 0.0


def calculate_allocation(holdings: List[Dict]) -> Dict[str, float]:
    """
    Calculate detailed asset allocation percentages
    
    Returns:
        Dict with allocation by type and category
    """
    total_value = sum(h.get('current_value', 0) for h in holdings)
    
    if total_value == 0:
        return {
            'equity': 0, 'debt': 0, 'hybrid': 0, 'gold': 0, 'other': 0,
            'large_cap': 0, 'mid_cap': 0, 'small_cap': 0, 'flexi_cap': 0
        }
    
    # Type-based allocation
    equity_value = sum(
        h.get('current_value', 0) for h in holdings 
        if 'equity' in h.get('type', '').lower()
    )
    debt_value = sum(
        h.get('current_value', 0) for h in holdings 
        if 'debt' in h.get('type', '').lower()
    )
    hybrid_value = sum(
        h.get('current_value', 0) for h in holdings 
        if 'hybrid' in h.get('type', '').lower() or 'balanced' in h.get('type', '').lower()
    )
    gold_value = sum(
        h.get('current_value', 0) for h in holdings 
        if 'gold' in h.get('type', '').lower()
    )
    other_value = total_value - equity_value - debt_value - hybrid_value - gold_value
    
    # Category-based allocation (for equity funds)
    large_cap = sum(
        h.get('current_value', 0) for h in holdings 
        if 'large' in h.get('scheme_name', '').lower() and 'equity' in h.get('type', '').lower()
    )
    mid_cap = sum(
        h.get('current_value', 0) for h in holdings 
        if 'mid' in h.get('scheme_name', '').lower() and 'equity' in h.get('type', '').lower()
    )
    small_cap = sum(
        h.get('current_value', 0) for h in holdings 
        if 'small' in h.get('scheme_name', '').lower() and 'equity' in h.get('type', '').lower()
    )
    flexi_cap = sum(
        h.get('current_value', 0) for h in holdings 
        if 'flexi' in h.get('scheme_name', '').lower() and 'equity' in h.get('type', '').lower()
    )
    
    return {
        # Type allocation
        'equity': round((equity_value / total_value) * 100, 2),
        'debt': round((debt_value / total_value) * 100, 2),
        'hybrid': round((hybrid_value / total_value) * 100, 2),
        'gold': round((gold_value / total_value) * 100, 2),
        'other': round((other_value / total_value) * 100, 2),
        
        # Category allocation (equity)
        'large_cap': round((large_cap / total_value) * 100, 2),
        'mid_cap': round((mid_cap / total_value) * 100, 2),
        'small_cap': round((small_cap / total_value) * 100, 2),
        'flexi_cap': round((flexi_cap / total_value) * 100, 2),
    }


def calculate_portfolio_metrics(holdings: List[Dict], transactions: List[Dict]) -> Dict:
    """
    Calculate comprehensive portfolio metrics
    
    Returns:
        Dict with all portfolio-level metrics
    """
    total_value = sum(h.get('current_value', 0) for h in holdings)
    total_invested = sum(h.get('cost_value', 0) for h in holdings)
    total_gain = total_value - total_invested
    
    # Calculate portfolio XIRR using weighted average
    portfolio_xirr = 0.0
    if total_value > 0:
        weighted_xirr = sum(
            h.get('xirr', 0) * h.get('current_value', 0) 
            for h in holdings
        ) / total_value
        portfolio_xirr = round(weighted_xirr, 2)
    
    # Get allocation
    allocation = calculate_allocation(holdings)
    
    # Find top and bottom performers
    sorted_holdings = sorted(
        holdings, 
        key=lambda x: x.get('gain_loss_percent', 0), 
        reverse=True
    )
    
    top_performers = [
        {
            'scheme_name': h['scheme_name'],
            'return_pct': h.get('gain_loss_percent', 0),
            'current_value': h.get('current_value', 0),
            'xirr': h.get('xirr', 0)
        }
        for h in sorted_holdings[:5]
    ]
    
    worst_performers = [
        {
            'scheme_name': h['scheme_name'],
            'return_pct': h.get('gain_loss_percent', 0),
            'current_value': h.get('current_value', 0),
            'xirr': h.get('xirr', 0)
        }
        for h in sorted_holdings[-5:]
    ]
    
    return {
        'total_value': total_value,
        'total_invested': total_invested,
        'total_gain': total_gain,
        'total_gain_percent': round((total_gain / total_invested * 100), 2) if total_invested > 0 else 0,
        'portfolio_xirr': portfolio_xirr,
        'allocation': allocation,
        'top_performers': top_performers,
        'worst_performers': worst_performers,
        'num_funds': len(holdings)
    }

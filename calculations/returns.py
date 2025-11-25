"""
Financial calculations for portfolio
"""
import pyxirr
from datetime import datetime, date
from typing import List, Dict
import pandas as pd

def calculate_xirr(transactions: List[Dict], current_value: float = 0.0) -> float:
    """
    Calculate XIRR (Extended Internal Rate of Return) for portfolio
    
    Args:
        transactions: List of transactions with 'date', 'amount', 'type'
        current_value: Current total value of the portfolio
        
    Returns:
        XIRR as percentage (e.g., 12.5 for 12.5%)
    """
    try:
        dates = []
        cash_flows = []
        
        for txn in transactions:
            txn_date = txn['date']
            if isinstance(txn_date, str):
                txn_date = datetime.strptime(txn_date, '%d-%b-%Y').date()
            
            dates.append(txn_date)
            
            # Purchases are negative cash flows
            # Redemptions are positive cash flows
            if txn['type'] in ['purchase', 'sip']:
                cash_flows.append(-abs(txn['amount']))
            elif txn['type'] in ['redemption']:
                cash_flows.append(abs(txn['amount']))
        
        # Add current portfolio value as final positive cash flow
        if current_value > 0:
            dates.append(date.today())
            cash_flows.append(current_value)
        
        if len(dates) > 1 and len(cash_flows) > 1:
            xirr_value = pyxirr.xirr(dates, cash_flows)
            if xirr_value is None:
                return 0.0
            return round(xirr_value * 100, 2)  # Convert to percentage
        
        return 0.0
        
    except Exception as e:
        print(f"Error calculating XIRR: {str(e)}")
        return 0.0

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

def calculate_absolute_return(invested: float, current: float) -> float:
    """Calculate simple absolute return percentage"""
    if invested <= 0:
        return 0.0
    
    return round(((current - invested) / invested) * 100, 2)

def calculate_allocation(holdings: List[Dict]) -> Dict[str, float]:
    """
    Calculate asset allocation percentages
    
    Returns:
        Dict with equity_pct, debt_pct, hybrid_pct, other_pct
    """
    total_value = sum(h.get('current_value', 0) for h in holdings)
    
    if total_value == 0:
        return {'equity': 0, 'debt': 0, 'hybrid': 0, 'other': 0}
    
    equity_value = sum(h.get('current_value', 0) for h in holdings if 'equity' in h.get('type', '').lower())
    debt_value = sum(h.get('current_value', 0) for h in holdings if 'debt' in h.get('type', '').lower())
    hybrid_value = sum(h.get('current_value', 0) for h in holdings if 'hybrid' in h.get('type', '').lower())
    other_value = total_value - equity_value - debt_value - hybrid_value
    
    return {
        'equity': round((equity_value / total_value) * 100, 2),
        'debt': round((debt_value / total_value) * 100, 2),
        'hybrid': round((hybrid_value / total_value) * 100, 2),
        'other': round((other_value / total_value) * 100, 2)
    }

def calculate_fund_wise_cagr(holdings: List[Dict], transactions: List[Dict]) -> List[Dict]:
    """Calculate CAGR for each fund"""
    fund_cagr = []
    
    for holding in holdings:
        scheme_name = holding['scheme_name']
        folio = holding['folio_number']
        
        # Get transactions for this fund
        fund_txns = [t for t in transactions 
                     if t.get('scheme_name') == scheme_name and t.get('folio_number') == folio]
        
        if not fund_txns:
            continue
        
        # Find first purchase date
        purchase_txns = [t for t in fund_txns if t['type'] == 'purchase']
        if not purchase_txns:
            continue
        
        first_purchase = min(purchase_txns, key=lambda x: x['date'])
        first_date = first_purchase['date']
        if isinstance(first_date, str):
            first_date = datetime.strptime(first_date, '%d-%b-%Y').date()
        
        # Calculate years held
        years = (date.today() - first_date).days / 365.25
        
        # Calculate invested amount for this fund
        invested = sum(t['amount'] for t in purchase_txns)
        current_value = holding.get('current_value', 0)
        
        if years > 0 and invested > 0:
            cagr = calculate_cagr(invested, current_value, years)
            fund_cagr.append({
                'scheme_name': scheme_name,
                'folio': folio,
                'cagr': cagr,
                'invested': invested,
                'current_value': current_value,
                'years_held': round(years, 2)
            })
    
    return fund_cagr


# Test
if __name__ == "__main__":
    # Test CAGR
    initial = 100000
    final = 150000
    years = 3
    
    cagr = calculate_cagr(initial, final, years)
    print(f"CAGR Test: ₹{initial:,} → ₹{final:,} in {years} years = {cagr}%")
    
    # Test absolute return
    abs_return = calculate_absolute_return(initial, final)
    print(f"Absolute Return: {abs_return}%")

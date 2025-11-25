"""
MF Central Excel Parser
Parses the detailed CAS report Excel file from MF Central
"""
import pandas as pd
from typing import Dict, List


def parse_mf_central_excel(excel_path: str) -> Dict:
    """
    Parse MF Central Excel detailed report
    
    Args:
        excel_path: Path to Excel file
        
    Returns:
        Dict with holdings data
    """
    # Read Excel file without header
    df = pd.read_excel(excel_path, header=None)
    
    # Header is at row 11 (0-indexed)
    header_row = 11
    
    # Extract summary data
    total_invested = float(df.iloc[9, 0]) if pd.notna(df.iloc[9, 0]) else 0
    total_current_value = float(df.iloc[9, 1]) if pd.notna(df.iloc[9, 1]) else 0
    total_profit_loss = float(df.iloc[9, 2]) if pd.notna(df.iloc[9, 2]) else 0
    
    # Set headers from row 11
    df.columns = df.iloc[header_row]
    df = df.iloc[header_row + 1:].reset_index(drop=True)
    
    # Remove empty rows
    df = df.dropna(subset=['Scheme Name'])
    
    # Parse holdings
    holdings = []
    for _, row in df.iterrows():
        scheme = row.get('Scheme Name')
        if pd.isna(scheme) or str(scheme).strip() == '':
            continue
            
        # Extract values with proper handling
        cost_value = float(row.get('Invested Value', 0) or 0)
        current_value = float(row.get('Current Value', 0) or 0)
        profit_loss = float(row.get('Profit/Loss', 0) or 0)
        units = float(row.get('Units', 0) or 0)
        
        # Skip only if both cost and current value are zero
        if cost_value == 0 and current_value == 0:
            continue
        
        holding = {
            'scheme_name': str(scheme).strip(),
            'amc': str(row.get('AMC Name', '')).strip(),
            'type': str(row.get('Category', 'EQUITY')).strip(),
            'folio_number': str(row.get('Folio No.', '')).strip(),
            'cost_value': cost_value,
            'current_value': current_value,
            'gain_loss': profit_loss,
            'units': units,
        }
        
        # Calculate derived fields
        holding['gain_loss_percent'] = (
            (holding['gain_loss'] / holding['cost_value'] * 100)
            if holding['cost_value'] > 0 else 0
        )
        holding['current_nav'] = (
            holding['current_value'] / holding['units']
            if holding['units'] > 0 else 0
        )
        
        holdings.append(holding)
    
    return {
        'holdings': holdings,
        'total_value': total_current_value,
        'total_invested': total_invested,
        'total_gain': total_profit_loss,
        'total_gain_percent': (total_profit_loss / total_invested * 100) if total_invested > 0 else 0,
        'num_funds': len(holdings),
        'data_source': 'MF Central Excel'
    }


if __name__ == "__main__":
    # Test
    result = parse_mf_central_excel('cas_detailed_report_2025_11_26_004753.xlsx')
    print(f"Total Holdings: {result['num_funds']}")
    print(f"Total Value: ₹{result['total_value']:,.2f}")
    print(f"Total Invested: ₹{result['total_invested']:,.2f}")
    print(f"Total Gain: ₹{result['total_gain']:,.2f} ({result['total_gain_percent']:.2f}%)")
    print(f"\nFirst 5 holdings:")
    for h in result['holdings'][:5]:
        print(f"  {h['scheme_name'][:50]:50s} | ₹{h['current_value']:>12,.2f}")

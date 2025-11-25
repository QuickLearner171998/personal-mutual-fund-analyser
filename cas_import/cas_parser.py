"""
CAS PDF Parser using casparser library
Handles CAMS, KFintech, CDSL, NSDL CAS formats
"""
import casparser
from typing import Dict, List, Optional
from datetime import datetime
import json

class CASParser:
    def __init__(self, pdf_path: str, password: str = ""):
        self.pdf_path = pdf_path
        self.password = password
        self.cas_data = None
        
    def parse(self) -> Dict:
        """Parse CAS PDF and return structured data"""
        try:
            # Parse CAS PDF - pass empty string for no password
            # casparser handles unencrypted PDFs automatically
            self.cas_data = casparser.read_cas_pdf(
                self.pdf_path,
                self.password if self.password else "",  # Empty string for unencrypted
                output='dict'
            )
            
            if not self.cas_data:
                raise ValueError("Failed to parse CAS PDF - returned None")
            
            print(f"✓ Parsed CAS for: {self.cas_data.get('investor_info', {}).get('name', 'Unknown')}")
            print(f"✓ Statement Period: {self.cas_data.get('statement_period', {}).get('from', '')} to {self.cas_data.get('statement_period', {}).get('to', '')}")
            print(f"✓ Found {len(self.cas_data.get('folios', []))} folios")
            
            return self.cas_data
            
        except Exception as e:
            print(f"✗ Error parsing CAS: {str(e)}")
            print(f"  Hint: CAS PDF might be in an unsupported format")
            print(f"  Try exporting CAS from MF Central or CAMS website")
            raise
    
    def extract_holdings(self) -> List[Dict]:
        """Extract current holdings from parsed CAS"""
        if not self.cas_data:
            raise ValueError("CAS not parsed. Call parse() first.")
        
        holdings = []
        
        for folio in self.cas_data.get('folios', []):
            fund_name = folio.get('scheme', 'Unknown')
            amc = folio.get('amc', 'Unknown')
            folio_number = folio.get('folio', '')
            
            for scheme in folio.get('schemes', []):
                holding = {
                    'scheme_name': scheme.get('scheme', fund_name),
                    'amc': amc,
                    'folio_number': folio_number,
                    'advisor': scheme.get('advisor', ''),
                    'rta_code': scheme.get('rta_code', ''),
                    'isin': scheme.get('isin', ''),
                    'amfi_code': scheme.get('amfi', ''),
                   'type': scheme.get('type', ''),  # EQUITY, DEBT, etc.
                    'units': float(scheme.get('close', 0)),  # Current balance
                    'nav': float(scheme.get('nav', 0)),
                    'value': float(scheme.get('valuation', {}).get('value', 0)),
                    'invested_value': 0,  # Will calculate from transactions
                    'transactions': scheme.get('transactions', [])
                }
                
                if holding['units'] > 0:  # Only include active holdings
                    holdings.append(holding)
        
        print(f"✓ Extracted {len(holdings)} active holdings")
        return holdings
    
    def extract_transactions(self) -> List[Dict]:
        """Extract all transactions from CAS"""
        if not self.cas_data:
            raise ValueError("CAS not parsed. Call parse() first.")
        
        all_transactions = []
        
        for folio in self.cas_data.get('folios', []):
            for scheme in folio.get('schemes', []):
                scheme_name = scheme.get('scheme', 'Unknown')
                folio_number = folio.get('folio', '')
                
                for txn in scheme.get('transactions', []):
                    transaction = {
                        'date': txn.get('date'),
                        'scheme_name': scheme_name,
                        'folio_number': folio_number,
                        'description': txn.get('description', ''),
                        'amount': float(txn.get('amount', 0)),
                        'units': float(txn.get('units', 0)),
                        'nav': float(txn.get('nav', 0)),
                        'balance': float(txn.get('balance', 0)),
                        'type': self._classify_transaction(txn.get('description', ''))
                    }
                    all_transactions.append(transaction)
        
        # Sort by date
        all_transactions.sort(key=lambda x: x['date'])
        
        print(f"✓ Extracted {len(all_transactions)} transactions")
        return all_transactions
    
    def _classify_transaction(self, description: str) -> str:
        """Classify transaction type from description"""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ['purchase', 'sip', 'switch in']):
            return 'purchase'
        elif any(word in desc_lower for word in ['redemption', 'switch out']):
            return 'redemption'
        elif 'dividend' in desc_lower:
            return 'dividend'
        else:
            return 'other'
    
    def get_summary(self) -> Dict:
        """Get portfolio summary from CAS"""
        if not self.cas_data:
            raise ValueError("CAS not parsed. Call parse() first.")
        
        investor_info = self.cas_data.get('investor_info', {})
        statement_period = self.cas_data.get('statement_period', {})
        
        return {
            'investor_name': investor_info.get('name', ''),
            'email': investor_info.get('email', ''),
            'mobile': investor_info.get('mobile', ''),
            'pan': self.cas_data.get('file_type', ''),  # Best guess for PAN
            'statement_from': statement_period.get('from', ''),
            'statement_to': statement_period.get('to', ''),
            'total_folios': len(self.cas_data.get('folios', [])),
        }


# Test the parser
if __name__ == "__main__":
    import sys
    
    pdf_path = "cas_detailed_report_2025_11_25_191935.pdf"
    password = ""  # CAS PDFs are usually not password protected
    
    parser = CASParser(pdf_path, password)
    
    try:
        print("\\n" + "="*50)
        print("  CAS PDF PARSER TEST")
        print("="*50 + "\\n")
        
        # Parse CAS
        cas_data = parser.parse()
        
        # Get summary
        summary = parser.get_summary()
        print("\\n📊 Investor Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        # Extract holdings
        print("\\n💼 Extracting Holdings...")
        holdings = parser.extract_holdings()
        print(f"\\n  Top 5 holdings by value:")
        sorted_holdings = sorted(holdings, key=lambda x: x['value'], reverse=True)[:5]
        for i, h in enumerate(sorted_holdings, 1):
            print(f"  {i}. {h['scheme_name'][:50]}")
            print(f"     Units: {h['units']:.2f} | NAV: ₹{h['nav']:.2f} | Value: ₹{h['value']:,.2f}")
        
        # Extract transactions
        print("\\n📝 Extracting Transactions...")
        transactions = parser.extract_transactions()
        print(f"\\n  Latest 5 transactions:")
        for i, txn in enumerate(transactions[-5:], 1):
            print(f"  {i}. {txn['date']} | {txn['type']} | ₹{txn['amount']:,.2f}")
            print(f"     {txn['scheme_name'][:50]}")
        
        print("\\n" + "="*50)
        print("  ✅ CAS PARSING SUCCESSFUL!")
        print("="*50 + "\\n")
        
    except Exception as e:
        print(f"\\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

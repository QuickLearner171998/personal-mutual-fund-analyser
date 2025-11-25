"""
Enhanced CAS PDF Parser - Redesigned for Complete Transaction Extraction
Handles MF Central detailed CAS format with ALL transaction history
"""
from pypdf import PdfReader
import re
from datetime import datetime
from typing import Dict, List, Tuple
from decimal import Decimal


class EnhancedCASParser:
    """
    Complete CAS parser that extracts:
    - All transactions with amounts, units, prices
    - Accurate invested value per fund
    - SIP details and schedules
    - Holdings with proper cost basis
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.full_text = ""
        self.folios = []
        
    def extract_text(self) -> str:
        """Extract complete text from all pages"""
        reader = PdfReader(self.pdf_path)
        print(f"✓ PDF has {len(reader.pages)} pages")
        
        for page in reader.pages:
            self.full_text += page.extract_text() + "\n"
        
        print(f"✓ Extracted {len(self.full_text)} characters")
        return self.full_text
    
    def parse_investor_info(self) -> Dict:
        """Extract investor details"""
        info = {}
        
        # PAN
        pan_match = re.search(r'PAN:\s*([A-Z]{5}\d{4}[A-Z])', self.full_text)
        if pan_match:
            info['pan'] = pan_match.group(1)
        
        # Name (line after PAN)
        name_match = re.search(r'PAN:\s*\w+\s*\n([^\n]+)', self.full_text)
        if name_match:
            info['name'] = name_match.group(1).strip()
        
        # Email
        email_match = re.search(r'Email:\s*([^\s\n]+@[^\s\n]+)', self.full_text)
        if email_match:
            info['email'] = email_match.group(1)
        
        # Mobile
        mobile_match = re.search(r'Mobile:\s*(\d{10})', self.full_text)
        if mobile_match:
            info['mobile'] = mobile_match.group(1)
        
        return info
    
    def parse_statement_period(self) -> Dict:
        """Extract statement period"""
        period = {}
        
        # From/To dates in header
        period_match = re.search(r'From Date\s*:\s*(\d{2}-[A-Za-z]{3}-\d{4}).*?To Date\s*:\s*(\d{2}-[A-Za-z]{3}-\d{4})', self.full_text)
        if period_match:
            period['from'] = period_match.group(1)
            period['to'] = period_match.group(2)
        
        return period
    
    def parse_holdings_and_transactions(self) -> Tuple[List[Dict], List[Dict]]:
        """
        Parse all folios with their holdings and transactions
        Returns: (holdings_list, transactions_list)
        """
        holdings = []
        all_transactions = []
        
        # Split by FOLIO NO
        folio_blocks = re.split(r'FOLIO NO:\s*(\w+)', self.full_text)
        
        for i in range(1, len(folio_blocks), 2):
            if i + 1 >= len(folio_blocks):
                break
                
            folio_number = folio_blocks[i].strip()
            folio_text = folio_blocks[i + 1]
            
            try:
                holding, transactions = self._parse_single_folio(folio_number, folio_text)
                if holding:
                    holdings.append(holding)
                    all_transactions.extend(transactions)
            except Exception as e:
                print(f"⚠ Error parsing folio {folio_number}: {str(e)}")
                continue
        
        return holdings, all_transactions
    
    def _parse_single_folio(self, folio_number: str, folio_text: str) -> Tuple[Dict, List[Dict]]:
        """Parse a single folio block"""
        
        # Extract scheme name (first line before ISIN)
        scheme_match = re.search(r'^(.+?)\s+\(Advisor:', folio_text, re.MULTILINE)
        if not scheme_match:
            scheme_match = re.search(r'^(.+?)\s+ISIN:', folio_text, re.MULTILINE)
        if not scheme_match:
            return None, []
        
        scheme_name = scheme_match.group(1).strip()
        scheme_name = re.sub(r'\s+', ' ', scheme_name)
        
        # Extract ISIN
        isin_match = re.search(r'ISIN:\s*(\w+)', folio_text)
        isin = isin_match.group(1) if isin_match else ''
        
        # Extract advisor/ARN
        advisor_match = re.search(r'Advisor:\s*([^)]+)\)', folio_text)
        advisor = advisor_match.group(1) if advisor_match else ''
        
        # Extract AMC from scheme name
        amc = self._extract_amc(scheme_name)
        
        # Fund type
        fund_type = self._classify_fund_type(scheme_name)
        
        # Parse ALL transactions for this folio
        transactions = self._parse_transactions(folio_text, scheme_name, folio_number)
        
        # Calculate invested value from purchase transactions
        invested_value = self._calculate_invested_value(transactions)
        
        # Get closing balance (units)
        closing_units = self._extract_closing_units(folio_text, transactions)
        
        # Get latest NAV and valuation
        nav, valuation = self._extract_nav_and_valuation(folio_text)
        
        holding = {
            'scheme_name': scheme_name,
            'folio_number': folio_number,
            'isin': isin,
            'amc': amc,
            'advisor': advisor,
            'type': fund_type,
            'units': closing_units,
            'current_nav': nav,
            'current_value': valuation,
            'invested_value': invested_value,
            'gain': valuation - invested_value if invested_value > 0 else 0,
            'gain_percent': ((valuation - invested_value) / invested_value * 100) if invested_value > 0 else 0,
            'num_transactions': len(transactions)
        }
        
        return holding, transactions
    
    def _parse_transactions(self, folio_text: str, scheme_name: str, folio: str) -> List[Dict]:
        """
        Parse all transactions from folio text
        Pattern: Date Description Amount Units Price UnitBalance
        """
        transactions = []
        
        # Transaction pattern: DD-MMM-YYYY Description Amount Units Price Balance
        # Handle parentheses for negative amounts
        pattern = r'(\d{2}-[A-Z]{3}-\d{4})\s+(.+?)\s+([\d,\.\-\(\)]+)\s+([\d,\.\-\(\)]+)\s+([\d,\.]+)\s+([\d,\.]+)(?=\s*\n|$)'
        
        matches = re.finditer(pattern, folio_text)
        
        for match in matches:
            try:
                date_str = match.group(1)
                description = match.group(2).strip()
                amount_str = match.group(3)
                units_str = match.group(4)
                price_str = match.group(5)
                balance_str = match.group(6)
                
                # Parse amounts (handle parentheses for negative)
                amount = self._parse_amount(amount_str)
                units = self._parse_amount(units_str)
                price = float(price_str.replace(',', ''))
                balance = float(balance_str.replace(',', ''))
                
                # Parse date
                date_obj = datetime.strptime(date_str, '%d-%b-%Y').date()
                
                # Classify transaction type
                txn_type = self._classify_transaction_type(description, amount)
                
                transaction = {
                    'date': date_obj,
                    'description': description,
                    'amount': amount,
                    'units': units,
                    'nav': price,
                    'balance': balance,
                    'type': txn_type,
                    'scheme_name': scheme_name,
                    'folio': folio
                }
                
                transactions.append(transaction)
                
            except Exception as e:
                # Skip malformed transactions
                continue
        
        return transactions
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string, handling parentheses for negative values"""
        amount_str = amount_str.strip()
        
        # Check if negative (parentheses)
        is_negative = amount_str.startswith('(') and amount_str.endswith(')')
        
        # Remove parentheses and commas
        amount_str = amount_str.strip('()').replace(',', '')
        
        try:
            value = float(amount_str)
            return -value if is_negative else value
        except:
            return 0.0
    
    def _classify_transaction_type(self, description: str, amount: float) -> str:
        """Classify transaction type from description"""
        desc_lower = description.lower()
        
        if 'redemption' in desc_lower or 'switch out' in desc_lower:
            return 'redemption'
        elif 'dividend' in desc_lower:
            return 'dividend'
        elif 'sip' in desc_lower or 'systematic' in desc_lower:
            return 'sip_purchase'
        elif 'purchase' in desc_lower:
            return 'purchase'
        elif 'switch in' in desc_lower:
            return 'switch_in'
        elif amount < 0:
            return 'redemption'
        elif amount > 0:
            return 'purchase'
        else:
            return 'other'
    
    def _calculate_invested_value(self, transactions: List[Dict]) -> float:
        """
        Calculate total invested amount from purchase transactions
        Purchases are positive amounts, redemptions are negative
        """
        invested = 0.0
        
        for txn in transactions:
            # Only count purchases (positive amounts)
            if txn['type'] in ['purchase', 'sip_purchase', 'switch_in'] and txn['amount'] > 0:
                invested += txn['amount']
            # Subtract redemptions (they reduce invested capital)
            elif txn['type'] in ['redemption', 'switch_out'] and txn['amount'] < 0:
                invested += txn['amount']  # Amount is already negative
        
        return max(invested, 0.0)  # Ensure non-negative
    
    def _extract_closing_units(self, folio_text: str, transactions: List[Dict]) -> float:
        """Extract closing unit balance"""
        # Try explicit closing balance
        closing_match = re.search(r'Closing Unit Balance:\s*([\d,\.]+)', folio_text)
        if closing_match:
            return float(closing_match.group(1).replace(',', ''))
        
        # Fallback: last transaction balance
        if transactions:
            return transactions[-1]['balance']
        
        return 0.0
    
    def _extract_nav_and_valuation(self, folio_text: str) -> Tuple[float, float]:
        """Extract NAV and valuation"""
        nav = 0.0
        valuation = 0.0
        
        # NAV pattern: "Nav as on DD-MMM-YYYY: INR X.XX"
        nav_match = re.search(r'Nav as on [^:]+:\s*INR\s*([\d,\.]+)', folio_text)
        if nav_match:
            nav = float(nav_match.group(1).replace(',', ''))
        
        # Valuation pattern: "Valuation on DD-MMM-YYYY : INR X,XXX.XX"
        val_match = re.search(r'Valuation on [^:]+:\s*INR\s*([\d,\.]+)', folio_text)
        if val_match:
            valuation = float(val_match.group(1).replace(',', ''))
        
        return nav, valuation
    
    def _extract_amc(self, scheme_name: str) -> str:
        """Extract AMC name from scheme"""
        amc_list = ['HDFC', 'ICICI', 'SBI', 'Axis', 'Kotak', 'Aditya Birla', 
                    'WhiteOak', 'DSP', 'Nippon', 'Franklin', 'Motilal Oswal',
                    'Tata', 'JioBlackRock', 'Parag Parikh', 'Quantum']
        
        for amc in amc_list:
            if amc.lower() in scheme_name.lower():
                return amc
        
        return ''
    
    def _classify_fund_type(self, scheme_name: str) -> str:
        """Classify fund type"""
        name_lower = scheme_name.lower()
        
        if any(word in name_lower for word in ['debt', 'liquid', 'gilt', 'bond', 'treasury']):
            return 'DEBT'
        elif any(word in name_lower for word in ['hybrid', 'balanced', 'multi asset']):
            return 'HYBRID'
        elif any(word in name_lower for word in ['gold', 'silver', 'commodity']):
            return 'COMMODITY'
        else:
            return 'EQUITY'
    
    def parse(self) -> Dict:
        """Main parse method"""
        print("\n" + "=" * 80)
        print("  ENHANCED CAS PARSER - Complete Transaction Extraction")
        print("=" * 80 + "\n")
        
        # Extract all text
        self.extract_text()
        
        # Parse investor info
        print("📋 Parsing investor information...")
        investor_info = self.parse_investor_info()
        print(f"  Name: {investor_info.get('name', 'Not found')}")
        print(f"  PAN: {investor_info.get('pan', 'Not found')}")
        
        # Parse period
        print("\n📅 Parsing statement period...")
        period = self.parse_statement_period()
        print(f"  From: {period.get('from')}")
        print(f"  To: {period.get('to')}")
        
        # Parse holdings and transactions
        print("\n💼 Parsing holdings and transactions...")
        holdings, transactions = self.parse_holdings_and_transactions()
        
        print(f"\n✓ Found {len(holdings)} funds")
        print(f"✓ Extracted {len(transactions)} total transactions")
        
        # Calculate totals
        total_value = sum(h['current_value'] for h in holdings)
        total_invested = sum(h['invested_value'] for h in holdings)
        total_gain = total_value - total_invested
        
        print(f"\n💰 Portfolio Summary:")
        print(f"  Total Value: ₹{total_value:,.2f}")
        print(f"  Total Invested: ₹{total_invested:,.2f}")
        print(f"  Total Gain: ₹{total_gain:,.2f} ({(total_gain/total_invested*100) if total_invested > 0 else 0:.2f}%)")
        
        return {
            'investor_info': investor_info,
            'statement_period': period,
            'holdings': holdings,
            'transactions': transactions,
            'summary': {
                'total_value': total_value,
                'total_invested': total_invested,
                'total_gain': total_gain,
                'num_funds': len(holdings),
                'num_transactions': len(transactions)
            }
        }


if __name__ == "__main__":
    import sys
    import json
    
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "cas_detailed_report_2025_11_25_193305.pdf"
    
    parser = EnhancedCASParser(pdf_path)
    result = parser.parse()
    
    # Save results
    with open('data/enhanced_cas_data.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str)
    
    print("\n✓ Saved to data/enhanced_cas_data.json")
    print("\n" + "=" * 80)
    print("  PARSING COMPLETE")
    print("=" * 80)

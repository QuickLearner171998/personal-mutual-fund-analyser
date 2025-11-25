"""
Custom CAS PDF Parser for MF Central format
Alternative to casparser when format detection fails
"""
from pypdf import PdfReader
import re
from datetime import datetime
from typing import Dict, List, Optional


class CustomCASParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text = ""
        self.pages = []
        
    def extract_text(self) -> str:
        """Extract all text from PDF"""
        try:
            reader = PdfReader(self.pdf_path)
            print(f"✓ PDF has {len(reader.pages)} pages")
            
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                self.pages.append(page_text)
                self.text += page_text + "\n"
            
            print(f"✓ Extracted {len(self.text)} characters")
            return self.text
            
        except Exception as e:
            print(f"✗ Error reading PDF: {str(e)}")
            raise
    
    def parse_investor_info(self) -> Dict:
        """Extract investor information"""
        investor_info = {
            'name': '',
            'pan': '',
            'email': '',
            'mobile': ''
        }
        
        # Look for PAN pattern
        pan_match = re.search(r'PAN[:\s]+([A-Z]{5}\d{4}[A-Z])', self.text)
        if pan_match:
            investor_info['pan'] = pan_match.group(1)
        
        # Look for name (usually after PAN)
        name_match = re.search(r'PAN[:\s]+\w+\s+(.+?)(?:\n|Email)', self.text, re.IGNORECASE)
        if name_match:
            investor_info['name'] = name_match.group(1).strip()
        
        # Look for email
        email_match = re.search(r'Email[:\s]+([\w\.-]+@[\w\.-]+)', self.text, re.IGNORECASE)
        if email_match:
            investor_info['email'] = email_match.group(1)
        
        # Look for mobile
        mobile_match = re.search(r'Mobile[:\s]+(\d{10})', self.text, re.IGNORECASE)
        if mobile_match:
            investor_info['mobile'] = mobile_match.group(1)
        
        return investor_info
    
    def parse_statement_period(self) -> Dict:
        """Extract statement period"""
        period = {'from': '', 'to': ''}
        
        # Look for "From Date" and "To Date"
        from_match = re.search(r'From Date[:\s]+(\d{2}-\w{3}-\d{4})', self.text, re.IGNORECASE)
        if from_match:
            period['from'] = from_match.group(1)
        
        to_match = re.search(r'To Date[:\s]+(\d{2}-\w{3}-\d{4})', self.text, re.IGNORECASE)
        if to_match:
            period['to'] = to_match.group(1)
        
        return period
    
    def parse_holdings(self) -> List[Dict]:
        """
        Extract holdings from MF Central CAS format
        Pattern: FOLIO NO: xxx followed by scheme details and closing balance
        """
        holdings = []
        
        # Split by FOLIO NO to get each fund
        folios = re.split(r'FOLIO NO[:\s]+', self.text)
        
        for folio_text in folios[1:]:  # Skip first split (before any folio)
            try:
                # Extract folio number (first word/number after split)
                folio_match = re.match(r'(\w+)', folio_text)
                if not folio_match:
                    continue
                folio_number = folio_match.group(1)
                
                # Extract scheme name (line after folio, before ISIN)
                scheme_match = re.search(r'\n(.+?)\(Advisor:', folio_text, re.DOTALL)
                if not scheme_match:
                    scheme_match = re.search(r'\n(.+?)ISIN:', folio_text, re.DOTALL)
                if not scheme_match:
                    continue
                    
                scheme_name = scheme_match.group(1).strip()
                scheme_name = re.sub(r'\s+', ' ', scheme_name)  # Clean whitespace
                
                # Extract ISIN
                isin_match = re.search(r'ISIN[:\s]+(\w+)', folio_text)
                isin = isin_match.group(1) if isin_match else ''
                
                # Extract AMC (from Fund name in header, if available)
                amc = ''
                for fund_name in ['WhiteOak', 'Aditya Birla', 'Kotak', 'ICICI', 'HDFC', 'SBI', 'Axis', 'DSP']:
                    if fund_name.lower() in scheme_name.lower():
                        amc = fund_name
                        break
                
                # Extract closing balance
                balance_match = re.search(r'Closing Unit Balance[:\s]+([\d,\.]+)', folio_text)
                if not balance_match:
                    continue
                units = float(balance_match.group(1).replace(',', ''))
                
                # Extract NAV
                nav_match = re.search(r'Nav as on [^:]+: INR ([\d,\.]+)', folio_text)
                current_nav = float(nav_match.group(1).replace(',', '')) if nav_match else 0.0
                
                # Extract valuation
                valuation_match = re.search(r'Valuation on [^:]+: INR ([\d,\.]+)', folio_text)
                current_value = float(valuation_match.group(1).replace(',', '')) if valuation_match else 0.0
                
                # Extract advisor
                advisor_match = re.search(r'Advisor[:\s]+([^)]+)', folio_text)
                advisor = advisor_match.group(1) if advisor_match else ''
                
                # Categorize by type
                fund_type = 'EQUITY'
                if any(word in scheme_name.lower() for word in ['debt', 'liquid', 'gilt', 'bond']):
                    fund_type = 'DEBT'
                elif any(word in scheme_name.lower() for word in ['hybrid', 'balanced', 'multi asset']):
                    fund_type = 'HYBRID'
                
                holding = {
                    'scheme_name': scheme_name,
                    'amc': amc,
                    'folio_number': folio_number,
                    'isin': isin,
                    'advisor': advisor,
                    'units': units,
                    'current_nav': current_nav,
                    'current_value': current_value,
                    'type': fund_type,
                    'invested_value': 0,  # Will calculate from transactions
                    'transactions': []  # Will add separately
                }
                
                holdings.append(holding)
                print(f"✓ Parsed: {scheme_name[:50]}... | Units: {units:.2f} | Value: ₹{current_value:,.0f}")
                
            except Exception as e:
                print(f"✗ Error parsing folio {folio_number if 'folio_number' in locals() else 'unknown'}: {str(e)}")
                continue
        
        return holdings
    
    def parse_transactions(self) -> List[Dict]:
        """
        Extract all transactions from the text
        Pattern: DATE Description Amount Units Price Unit Balance
        """
        transactions = []
        
        # Match transaction lines (date at start, then description, amounts, units, nav, balance)
        # Example: 28-APR-2025 Systematic Purchase-NSE - Instalment No - 4/480 Online 4,999.75 365.532 13.68 1,509.430
        txn_pattern = r'(\d{2}-[A-Z]{3}-\d{4})\s+([^\d]+?)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)'
        
        matches = re.findall(txn_pattern, self.text)
        
        # We also need to associate transactions with schemes
        # For simplicity, we'll parse them generically
        for match in matches:
            try:
                date_str = match[0]
                description = match[1].strip()
                amount = float(match[2].replace(',', ''))
                units = float(match[3].replace(',', ''))
                nav = float(match[4].replace(',', ''))
                balance = float(match[5].replace(',', ''))
                
                # Classify transaction type
                txn_type = 'purchase'
                if 'redemption' in description.lower() or 'switch out' in description.lower():
                    txn_type = 'redemption'
                elif 'dividend' in description.lower():
                    txn_type = 'dividend'
                
                # Parse date
                date_obj = datetime.strptime(date_str, '%d-%b-%Y').date()
                
                transaction = {
                    'date': date_obj,
                    'description': description,
                    'amount': amount,
                    'units': units,
                    'nav': nav,
                    'balance': balance,
                    'type': txn_type
                }
                
                transactions.append(transaction)
                
            except Exception as e:
                continue  # Skip malformed transactions
        
        print(f"✓ Extracted {len(transactions)} transactions")
        return transactions
    
    def parse(self) -> Dict:
        """Main parse method"""
        print("\n" + "="*60)
        print("  CUSTOM CAS PARSER - MF Central Format")
        print("="*60 + "\n")
        
        # Extract text
        self.extract_text()
        
        # Parse components
        print("\n📋 Parsing investor information...")
        investor_info = self.parse_investor_info()
        print(f"  Name: {investor_info.get('name', 'Not found')}")
        print(f"  PAN: {investor_info.get('pan', 'Not found')}")
        print(f"  Email: {investor_info.get('email', 'Not found')}")
        
        print("\n📅 Parsing statement period...")
        period = self.parse_statement_period()
        print(f"  From: {period.get('from', 'Not found')}")
        print(f"  To: {period.get('to', 'Not found')}")
        
        print("\n💼 Parsing holdings...")
        holdings = self.parse_holdings()
        print(f"\n✓ Found {len(holdings)} funds")
        
        print("\n📝 Parsing transactions...")
        transactions = self.parse_transactions()
        
        # Calculate total portfolio value
        total_value = sum(h.get('current_value', 0) for h in holdings)
        print(f"\n💰 Total Portfolio Value: ₹{total_value:,.2f}")
        
        # Save extracted text for manual inspection
        with open('data/cas_extracted_text.txt', 'w', encoding='utf-8') as f:
            f.write(self.text)
        print(f"\n✓ Saved extracted text to: data/cas_extracted_text.txt")
        
        # Save parsed data as JSON
        import json
        parsed_data = {
            'investor_info': investor_info,
            'statement_period': period,
            'holdings': holdings,
            'num_holdings': len(holdings),
            'total_value': total_value,
            'num_transactions': len(transactions)
        }
        
        with open('data/cas_parsed_data.json', 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, indent=2, default=str)
        print(f"✓ Saved parsed data to: data/cas_parsed_data.json")
        
        return {
            'investor_info': investor_info,
            'statement_period': period,
            'holdings': holdings,
            'transactions': transactions,
            'raw_text': self.text
        }


if __name__ == "__main__":
    pdf_path = "cas_detailed_report_2025_11_25_191935.pdf"
    
    parser = CustomCASParser(pdf_path)
    result = parser.parse()
    
    print("\n" + "="*60)
    print("  PARSING COMPLETE")
    print("="*60)

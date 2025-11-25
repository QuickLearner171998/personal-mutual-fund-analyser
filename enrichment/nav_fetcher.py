"""
NAV Fetcher - Get latest NAV from MF API
"""
import requests
from typing import Dict, Optional
from datetime import datetime, timedelta
import json

class NAVFetcher:
    BASE_URL = "https://api.mfapi.in/mf"
    
    def __init__(self):
        self.cache = {}  # Simple in-memory cache
        
    def fetch_nav(self, scheme_code: str) -> Optional[Dict]:
        """Fetch latest NAV for a scheme code"""
        try:
            url = f"{self.BASE_URL}/{scheme_code}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data and 'data' in data and len(data['data']) > 0:
                    latest = data['data'][0]  # First element is latest
                    return {
                        'scheme_code': scheme_code,
                        'scheme_name': data.get('meta', {}).get('scheme_name', ''),
                        'nav': float(latest.get('nav', 0)),
                        'date': latest.get('date', ''),
                        'scheme_type': data.get('meta', {}).get('scheme_type', ''),
                        'fund_house': data.get('meta', {}).get('fund_house', '')
                    }
        except Exception as e:
            print(f"Error fetching NAV for {scheme_code}: {str(e)}")
        
        return None
    
    def search_scheme(self, scheme_name: str) -> Optional[str]:
        """
        Search for scheme code by scheme name
        Note: MFAPI doesn't have direct search, so this would need
        a local database of scheme codes or AMFI scraping
        For now, return None - we'll get scheme codes from CAS
        """
        return None
    
    def enrich_holdings_with_nav(self, holdings: list) -> list:
        """Update holdings with latest NAV"""
        enriched = []
        
        for holding in holdings:
            scheme_code = holding.get('amfi_code', '')
            
            if scheme_code:
                nav_data = self.fetch_nav(scheme_code)
                
                if nav_data:
                    holding['current_nav'] = nav_data['nav']
                    holding['nav_date'] = nav_data['date']
                    holding['current_value'] = holding['units'] * nav_data['nav']
                    print(f"✓ Updated NAV for {holding['scheme_name'][:40]}: ₹{nav_data['nav']}")
                else:
                    print(f"✗ Could not fetch NAV for {holding['scheme_name'][:40]}")
            
            enriched.append(holding)
        
        return enriched


if __name__ == "__main__":
    # Test NAV fetcher
    fetcher = NAVFetcher()
    
    # Test with a known scheme code (SBI Bluechip Fund)
    test_scheme_code = "119551"
    
    print("Testing NAV Fetcher...")
    print("=" * 50)
    
    nav_data = fetcher.fetch_nav(test_scheme_code)
    
    if nav_data:
        print(f"✓ Scheme: {nav_data['scheme_name']}")
        print(f"✓ NAV: ₹{nav_data['nav']}")
        print(f"✓ Date: {nav_data['date']}")
        print(f"✓ Fund House: {nav_data['fund_house']}")
    else:
        print("✗ Failed to fetch NAV")

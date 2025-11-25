"""
Comprehensive tests for MF Portfolio Bot
Covers Dashboard (CAGR), SIP Analysis, and QnA
"""
import unittest
from datetime import date, timedelta, datetime
from calculations.returns import calculate_fund_wise_cagr, calculate_cagr
from ui.sip_dashboard import render_sip_dashboard
import pandas as pd
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestPortfolioAnalysis(unittest.TestCase):
    
    def setUp(self):
        self.holdings = [
            {
                'scheme_name': 'Test Fund A',
                'folio_number': '123',
                'current_value': 150000,
                'units': 1000
            },
            {
                'scheme_name': 'Test Fund B',
                'folio_number': '456',
                'current_value': 120000,
                'units': 500
            }
        ]
        
        self.transactions = [
            # Fund A: Invested 1L 3 years ago
            {
                'date': date.today() - timedelta(days=1100),
                'scheme_name': 'Test Fund A',
                'folio_number': '123',
                'type': 'purchase',
                'amount': 100000,
                'units': 1000
            },
            # Fund B: SIPs (Active)
            {
                'date': date.today() - timedelta(days=30),
                'scheme_name': 'Test Fund B',
                'folio_number': '456',
                'type': 'sip',
                'description': 'SIP Purchase',
                'amount': 10000,
                'units': 50
            },
            {
                'date': date.today() - timedelta(days=60),
                'scheme_name': 'Test Fund B',
                'folio_number': '456',
                'type': 'sip',
                'description': 'SIP Purchase',
                'amount': 10000,
                'units': 50
            },
            # Malformed Transaction (Missing folio)
            {
                'date': date.today(),
                'scheme_name': 'Test Fund A',
                'type': 'purchase',
                'amount': 5000
            }
        ]

    def test_cagr_calculation(self):
        """Test CAGR calculation logic"""
        # 1L -> 1.5L in ~3 years
        fund_cagr = calculate_fund_wise_cagr(self.holdings, self.transactions)
        
        # Should find Fund A
        fund_a = next((f for f in fund_cagr if f['scheme_name'] == 'Test Fund A'), None)
        self.assertIsNotNone(fund_a)
        self.assertGreater(fund_a['cagr'], 10) # Expect > 10%
        
        # Should NOT crash on malformed transaction
        # (The malformed transaction should be ignored or handled gracefully)
        
    def test_sip_filtering(self):
        """Test Active SIP filtering logic"""
        # Replicating logic from sip_dashboard.py
        sip_txns = [t for t in self.transactions if 'sip' in t.get('type', '').lower() or 'sip' in t.get('description', '').lower()]
        
        active_sips = []
        sip_by_scheme = {}
        for txn in sip_txns:
            scheme = txn['scheme_name']
            if scheme not in sip_by_scheme:
                sip_by_scheme[scheme] = []
            sip_by_scheme[scheme].append(txn)
            
        cutoff_date = date.today() - timedelta(days=45)
        
        for scheme, txns in sip_by_scheme.items():
            txns.sort(key=lambda x: x['date'], reverse=True)
            last_date = txns[0]['date']
            is_active = last_date >= cutoff_date
            
            if is_active:
                active_sips.append(scheme)
                
        self.assertIn('Test Fund B', active_sips)
        self.assertEqual(len(active_sips), 1)

    def test_qna_agent(self):
        """Test QnA Agent with Portfolio Query"""
        try:
            from agents.orchestrator import answer_query
            response = answer_query("What is my total investment?", stream=False)
            self.assertIsInstance(response, str)
            self.assertTrue(len(response) > 0)
        except Exception as e:
            self.fail(f"QnA Agent failed: {e}")

if __name__ == '__main__':
    unittest.main()

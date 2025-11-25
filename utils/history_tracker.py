"""
Historical Portfolio Tracker
Stores daily snapshots for timeline analysis
"""
import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional
from database.json_store import PortfolioStore

class HistoryTracker:
    def __init__(self, history_dir='./data/portfolio_history'):
        self.history_dir = history_dir
        os.makedirs(history_dir, exist_ok=True)
        self.store = PortfolioStore()
    
    def save_snapshot(self, custom_date: Optional[date] = None):
        """Save current portfolio as historical snapshot"""
        portfolio = self.store.get_portfolio()
        
        if not portfolio:
            return None
        
        # Use custom date or today
        snapshot_date = custom_date or date.today()
        filename = f"{self.history_dir}/{snapshot_date.isoformat()}.json"
        
        # Add snapshot metadata
        snapshot = {
            'date': snapshot_date.isoformat(),
            'total_value': portfolio.get('total_value'),
            'total_invested': portfolio.get('total_invested'),
            'total_gain': portfolio.get('total_gain'),
            'xirr': portfolio.get('xirr'),
            'allocation': portfolio.get('allocation'),
            'num_funds': len(portfolio.get('holdings', []))
        }
        
        with open(filename, 'w') as f:
            json.dump(snapshot, f, indent=2)
        
        print(f"✓ Saved snapshot for {snapshot_date}")
        return snapshot
    
    def get_snapshot(self, snapshot_date: date) -> Optional[Dict]:
        """Load specific snapshot"""
        filename = f"{self.history_dir}/{snapshot_date.isoformat()}.json"
        
        if not os.path.exists(filename):
            return None
        
        with open(filename, 'r') as f:
            return json.load(f)
    
    def get_timeline_data(self, days: int = 365) -> List[Dict]:
        """Get timeline data for charts"""
        from datetime import timedelta
        
        timeline = []
        current_date = date.today()
        
        for i in range(days, -1, -1):
            check_date = current_date - timedelta(days=i)
            snapshot = self.get_snapshot(check_date)
            
            if snapshot:
                timeline.append(snapshot)
        
        return timeline
    
    def backfill_history(self, transactions: List[Dict], holdings: List[Dict]):
        """
        Backfill history for 1m, 3m, 6m, 1y, 3y using historical NAVs
        This enables 'Period Returns' to work immediately after upload
        """
        from enrichment.nav_fetcher import NAVFetcher
        from datetime import timedelta
        
        print("⏳ Backfilling portfolio history...")
        fetcher = NAVFetcher()
        
        # Target dates to backfill
        target_periods = [30, 90, 180, 365, 365*3]
        target_dates = [date.today() - timedelta(days=d) for d in target_periods]
        
        # Cache NAV history for all schemes
        nav_history_cache = {}
        for holding in holdings:
            scheme_code = holding.get('amfi_code')
            if scheme_code and scheme_code not in nav_history_cache:
                nav_history_cache[scheme_code] = fetcher.fetch_nav_history(scheme_code)
                print(f"   Fetched history for {holding['scheme_name'][:30]}...")
        
        # Process each target date
        for target_date in target_dates:
            # Check if snapshot already exists
            if self.get_snapshot(target_date):
                continue
                
            total_value = 0
            total_invested = 0
            
            # Calculate portfolio state on target_date
            for holding in holdings:
                scheme_name = holding['scheme_name']
                scheme_code = holding.get('amfi_code')
                folio = holding.get('folio_number')
                
                # 1. Calculate units held on target_date
                units = 0
                invested = 0
                
                # Filter transactions up to target_date
                relevant_txns = [
                    t for t in transactions 
                    if t.get('scheme_name') == scheme_name 
                    and t.get('folio_number') == folio
                ]
                
                for txn in relevant_txns:
                    txn_date = txn['date']
                    if isinstance(txn_date, str):
                        txn_date = datetime.strptime(txn_date, '%d-%b-%Y').date()
                    
                    if txn_date <= target_date:
                        if txn['type'] in ['purchase', 'sip']:
                            units += txn['units']
                            invested += txn['amount']
                        elif txn['type'] == 'redemption':
                            units -= txn['units']
                            invested -= txn['amount'] # Simplified
                
                if units > 0.01: # If held units
                    # 2. Find NAV on target_date
                    nav = 0
                    if scheme_code in nav_history_cache:
                        history = nav_history_cache[scheme_code]
                        # Find closest NAV <= target_date
                        # History is usually sorted desc (newest first)
                        for entry in history:
                            nav_date = datetime.strptime(entry['date'], '%d-%m-%Y').date()
                            if nav_date <= target_date:
                                nav = float(entry['nav'])
                                break
                    
                    if nav > 0:
                        total_value += units * nav
                        total_invested += invested
            
            if total_value > 0:
                # Save snapshot
                self.save_snapshot_data(target_date, {
                    'date': target_date.isoformat(),
                    'total_value': round(total_value, 2),
                    'total_invested': round(total_invested, 2),
                    'total_gain': round(total_value - total_invested, 2),
                    'xirr': 0, # Skipping XIRR for backfill to save time
                    'allocation': {},
                    'num_funds': 0 # Placeholder
                })
                print(f"✓ Backfilled snapshot for {target_date}: ₹{total_value:,.0f}")

    def save_snapshot_data(self, snapshot_date: date, data: Dict):
        """Internal method to save snapshot data directly"""
        filename = f"{self.history_dir}/{snapshot_date.isoformat()}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def calculate_period_return(self, days: int) -> Optional[float]:
        """Calculate return for specific period (e.g., 30, 90, 180, 365 days)"""
        from datetime import timedelta
        
        current_portfolio = self.store.get_portfolio()
        if not current_portfolio:
            return None
        
        past_date = date.today() - timedelta(days=days)
        past_snapshot = self.get_snapshot(past_date)
        
        if not past_snapshot:
            return None
        
        past_value = past_snapshot.get('total_value', 0)
        current_value = current_portfolio.get('total_value', 0)
        
        if past_value == 0:
            return None
        
        # Use CAGR for periods >= 1 year
        if days >= 365:
            from calculations.returns import calculate_cagr
            years = days / 365.25
            return calculate_cagr(past_value, current_value, years)
            
        return ((current_value - past_value) / past_value) * 100


# Global instance
tracker = HistoryTracker()

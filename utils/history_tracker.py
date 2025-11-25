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
        
        return ((current_value - past_value) / past_value) * 100


# Global instance
tracker = HistoryTracker()

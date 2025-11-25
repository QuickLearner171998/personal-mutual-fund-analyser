"""
Simple JSON file storage for portfolio data
No MongoDB required
"""
import json
from typing import Dict, List, Optional
from datetime import datetime
import os

class PortfolioStore:
    def __init__(self, data_dir='./data'):
        self.data_dir = data_dir
        self.portfolio_file = f"{data_dir}/portfolio.json"
        self.transactions_file = f"{data_dir}/transactions.json"
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
    def save_portfolio(self, portfolio_data: Dict) -> str:
        """Save or update portfolio to JSON file"""
        portfolio_data['last_updated'] = datetime.now().isoformat()
        
        with open(self.portfolio_file, 'w') as f:
            json.dump(portfolio_data, f, indent=2, default=str)
        
        return "saved"
    
    def get_portfolio(self) -> Optional[Dict]:
        """Get current portfolio from JSON file"""
        if not os.path.exists(self.portfolio_file):
            return None
            
        with open(self.portfolio_file, 'r') as f:
            return json.load(f)
    
    def save_transactions(self, transactions: List[Dict]) -> int:
        """Save transactions to JSON file"""
        if transactions:
            with open(self.transactions_file, 'w') as f:
                json.dump(transactions, f, indent=2, default=str)
            return len(transactions)
        return 0
    
    def get_transactions(self) -> List[Dict]:
        """Get all transactions from JSON file"""
        if not os.path.exists(self.transactions_file):
            return []
            
        with open(self.transactions_file, 'r') as f:
            return json.load(f)

"""
Enhanced JSON storage for MF Central portfolio data
"""
import json
from typing import Dict, List, Optional
from datetime import datetime, date
import os


class PortfolioStore:
    """Enhanced storage for MF Central data"""
    
    def __init__(self, data_dir='./data'):
        self.data_dir = data_dir
        self.portfolio_file = f"{data_dir}/portfolio.json"
        self.transactions_file = f"{data_dir}/transactions.json"
        self.sips_file = f"{data_dir}/sips.json"
        self.brokers_file = f"{data_dir}/brokers.json"
        self.aggregation_file = f"{data_dir}/aggregation_map.json"
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
    
    def save_portfolio(self, portfolio_data: Dict) -> str:
        """Save complete portfolio data"""
        portfolio_data['last_updated'] = datetime.now().isoformat()
        
        with open(self.portfolio_file, 'w') as f:
            json.dump(portfolio_data, f, indent=2, default=self._json_serializer)
        
        return "saved"
    
    def get_portfolio(self) -> Optional[Dict]:
        """Get current portfolio"""
        if not os.path.exists(self.portfolio_file):
            return None
        
        with open(self.portfolio_file, 'r') as f:
            return json.load(f)
    
    def save_transactions(self, transactions: List[Dict]) -> int:
        """Save all transactions"""
        if transactions:
            with open(self.transactions_file, 'w') as f:
                json.dump(transactions, f, indent=2, default=self._json_serializer)
            return len(transactions)
        return 0
    
    def get_transactions(self) -> List[Dict]:
        """Get all transactions"""
        if not os.path.exists(self.transactions_file):
            return []
        
        with open(self.transactions_file, 'r') as f:
            return json.load(f)
    
    def save_sips(self, sips: List[Dict]) -> int:
        """Save active SIP details"""
        if sips:
            with open(self.sips_file, 'w') as f:
                json.dump(sips, f, indent=2, default=self._json_serializer)
            return len(sips)
        return 0
    
    def get_sips(self) -> List[Dict]:
        """Get active SIPs"""
        if not os.path.exists(self.sips_file):
            return []
        
        with open(self.sips_file, 'r') as f:
            return json.load(f)
    
    def save_brokers(self, broker_info: Dict) -> int:
        """Save broker information"""
        if broker_info:
            with open(self.brokers_file, 'w') as f:
                json.dump(broker_info, f, indent=2, default=self._json_serializer)
            return len(broker_info)
        return 0
    
    def get_brokers(self) -> Dict:
        """Get broker information"""
        if not os.path.exists(self.brokers_file):
            return {}
        
        with open(self.brokers_file, 'r') as f:
            return json.load(f)
    
    def save_aggregation_map(self, aggregation_map: Dict) -> int:
        """Save fund aggregation mapping"""
        if aggregation_map:
            with open(self.aggregation_file, 'w') as f:
                json.dump(aggregation_map, f, indent=2, default=self._json_serializer)
            return len(aggregation_map)
        return 0
    
    def get_aggregation_map(self) -> Dict:
        """Get fund aggregation mapping"""
        if not os.path.exists(self.aggregation_file):
            return {}
        
        with open(self.aggregation_file, 'r') as f:
            return json.load(f)
    
    def save_complete_data(
        self,
        portfolio: Dict,
        transactions: List[Dict],
        sips: List[Dict],
        broker_info: Dict,
        aggregation_map: Dict
    ) -> Dict:
        """
        Save all data at once
        Returns summary of saved data
        """
        summary = {
            'portfolio': self.save_portfolio(portfolio),
            'transactions': self.save_transactions(transactions),
            'sips': self.save_sips(sips),
            'brokers': self.save_brokers(broker_info),
            'aggregation_map': self.save_aggregation_map(aggregation_map),
            'timestamp': datetime.now().isoformat()
        }
        
        return summary
    
    def get_complete_data(self) -> Dict:
        """
        Get all data at once
        Returns dict with all portfolio data
        """
        return {
            'portfolio': self.get_portfolio(),
            'transactions': self.get_transactions(),
            'sips': self.get_sips(),
            'brokers': self.get_brokers(),
            'aggregation_map': self.get_aggregation_map()
        }
    
    def clear_all_data(self) -> bool:
        """Clear all stored data"""
        try:
            files = [
                self.portfolio_file,
                self.transactions_file,
                self.sips_file,
                self.brokers_file,
                self.aggregation_file
            ]
            
            for file_path in files:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            return True
        except Exception as e:
            print(f"Error clearing data: {str(e)}")
            return False
    
    @staticmethod
    def _json_serializer(obj):
        """Custom JSON serializer for datetime objects"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

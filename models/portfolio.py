"""
Enhanced Portfolio data models for MF Central data
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date, datetime


class SIPDetails(BaseModel):
    """Active SIP details"""
    scheme_name: str
    folio_number: str
    sip_amount: float
    frequency: str  # Monthly, Quarterly, Weekly, Yearly
    start_date: date
    last_installment_date: date
    next_installment_date: Optional[date] = None
    total_installments: int
    total_invested: float
    is_active: bool = True
    broker: str = ""


class MFHolding(BaseModel):
    """Single mutual fund holding with enhanced fields"""
    scheme_name: str
    amc: str = ""
    folio_number: str
    scheme_code: Optional[str] = None
    
    # Unit and value information
    units: float
    current_nav: float = 0.0
    current_value: float = 0.0
    cost_value: float = 0.0  # Total invested amount
    gain_loss: float = 0.0
    gain_loss_percent: float = 0.0
    
    # Classification
    type: str = ""  # Equity, Debt, Hybrid, Gold FOF, etc.
    category: str = ""  # Large Cap, Mid Cap, Small Cap, etc.
    
    # Performance metrics
    xirr: float = 0.0  # Fund-specific XIRR
    cagr_1y: Optional[float] = None
    cagr_3y: Optional[float] = None
    cagr_5y: Optional[float] = None
    
    # Metadata
    nav_date: Optional[date] = None
    broker: str = ""
    is_direct: bool = False
    is_aggregated: bool = False
    aggregated_folios: List[str] = []
    
    # Investor info
    investor_name: str = ""
    pan: str = ""


class Transaction(BaseModel):
    """Single transaction"""
    trade_date: date
    scheme_name: str
    folio_number: str
    transaction_type: str  # purchase, sip, redemption, switch_in, switch_out, dividend
    amount: float
    units: float
    price: float  # NAV at transaction
    broker: str = ""
    mf_name: str = ""
    product_code: str = ""


class BrokerInfo(BaseModel):
    """Broker/Intermediary information"""
    broker_name: str
    total_invested: float
    scheme_count: int
    schemes: List[str]
    transaction_count: int
    first_transaction: Optional[date] = None
    last_transaction: Optional[date] = None


class Portfolio(BaseModel):
    """Complete portfolio with MF Central data"""
    # Investor information
    investor_name: str = ""
    pan: str = ""
    
    # Portfolio totals
    total_value: float = 0.0
    total_invested: float = 0.0
    total_gain: float = 0.0
    total_gain_percent: float = 0.0
    xirr: Optional[float] = None
    
    # Holdings
    holdings: List[MFHolding] = []
    aggregated_holdings: List[MFHolding] = []
    
    # SIPs
    active_sips: List[SIPDetails] = []
    
    # Broker information
    broker_info: Dict[str, Dict] = {}
    
    # Aggregation mapping
    aggregation_map: Dict[str, Dict] = {}
    
    # Counts
    num_funds: int = 0
    num_aggregated_funds: int = 0
    num_active_sips: int = 0
    num_brokers: int = 0
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.now)
    data_source: str = "MF Central"
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class PortfolioSummary(BaseModel):
    """Summary metrics for dashboard"""
    total_current_value: float
    total_invested: float
    total_gain: float
    total_gain_percent: float
    xirr: Optional[float]
    num_funds: int
    num_active_sips: int
    num_brokers: int
    
    # Asset allocation
    equity_allocation: float = 0.0
    debt_allocation: float = 0.0
    hybrid_allocation: float = 0.0
    other_allocation: float = 0.0
    
    # Top performers
    top_performers: List[Dict] = []
    worst_performers: List[Dict] = []
    
    # SIP summary
    monthly_sip_amount: float = 0.0
    total_sip_invested: float = 0.0

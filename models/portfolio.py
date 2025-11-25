"""
Portfolio data models using Pydantic
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime

class MFHolding(BaseModel):
    """Single mutual fund holding"""
    scheme_name: str
    amc: str = ""
    folio_number: str
    isin: Optional[str] = None
    amfi_code: Optional[str] = None
    rta_code: Optional[str] = None
    units: float
    avg_cost: float = 0.0  # Average purchase NAV
    current_nav: float = 0.0
    current_value: float = 0.0
    invested_value: float = 0.0
    gain_loss: float = 0.0
    gain_loss_percent: float = 0.0
    category: str = ""  # Equity, Debt, Hybrid
    sub_category: str = ""  # Large Cap, Mid Cap, etc.
    
class Transaction(BaseModel):
    """Single transaction"""
    date: date
    scheme_name: str
    folio_number: str
    type: str  # purchase, redemption, dividend
    amount: float
    units: float
    nav: float
    balance: float = 0.0
    description: str = ""

class Portfolio(BaseModel):
    """Complete portfolio"""
    investor_name: str = ""
    pan: str = ""
    total_value: float = 0.0
    total_invested: float = 0.0
    total_gain: float = 0.0
    total_gain_percent: float = 0.0
    xirr: Optional[float] = None
    holdings: List[MFHolding] = []
    last_updated: datetime = Field(default_factory=datetime.now)
    statement_period_from: Optional[date] = None
    statement_period_to: Optional[date] = None

class PortfolioSummary(BaseModel):
    """Summary metrics for dashboard"""
    total_current_value: float
    total_invested: float
    total_gain: float
    total_gain_percent: float
    xirr: Optional[float]
    num_funds: int
    equity_allocation: float
    debt_allocation: float
    hybrid_allocation: float
    top_performers: List[Dict] = []
    worst_performers: List[Dict] = []

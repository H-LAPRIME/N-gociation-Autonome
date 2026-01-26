from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class Financials(BaseModel):
    max_budget_mad: float = 0.0
    preferred_payment: str = "Cash"
    monthly_limit_mad: Optional[float] = None
    current_debts_mad: float = 0.0
    is_blacklisted: bool = False
    contract_type: str = "Unknown"

class Preferences(BaseModel):
    brands: List[str] = []
    category: Optional[str] = None 
    fuel_type: str = "Diesel"
    usage: Optional[str] = None # New: For "usage" task in PDF

class User(BaseModel):
    user_id: int
    username: str
    email: str
    full_name: str
    phone_number: Optional[str] = None
    city: str = "Casablanca"
    income_mad: float
    
    financials: Financials
    preferences: Preferences
    risk_level: RiskLevel = RiskLevel.MEDIUM
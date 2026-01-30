from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class Financials(BaseModel):
    max_budget_mad: Optional[float] = None
    preferred_payment: Optional[str] = None
    monthly_limit_mad: Optional[float] = None
    current_debts_mad: Optional[float] = None
    is_blacklisted: Optional[bool] = None
    contract_type: Optional[str] = None
    bank_seniority_months: Optional[int] = None

class Preferences(BaseModel):
    brands: List[str] = Field(default_factory=list)
    category: Optional[str] = None 
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    usage: Optional[str] = None

class BehavioralAnalysis(BaseModel):
    sentiment: Optional[str] = None
    urgency: Optional[str] = None
    flexibility: Optional[float] = None
    detected_needs: List[str] = Field(default_factory=list)

class TradeInInfo(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    mileage: Optional[int] = None
    condition: Optional[str] = None
    accidents: Optional[bool] = None
    maintenance: Optional[str] = None
    owners: Optional[int] = None

class User(BaseModel):
    user_id: int
    username: str
    email: str
    full_name: str
    phone_number: Optional[str] = None
    city: Optional[str] = None
    income_mad: float
    
    financials: Optional[Financials] = None
    preferences: Optional[Preferences] = None
    risk_level: Optional[RiskLevel] = None
    behavior: Optional[BehavioralAnalysis] = None
    trade_in: Optional[TradeInInfo] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    city: Optional[str] = None
    income_mad: Optional[float] = 0
    financials: Optional[Financials] = None
    preferences: Optional[Preferences] = None
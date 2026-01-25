from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from enum import Enum

class RiskLevel(str, Enum):
    CONSERVATIVE = "conservative"  # Wants "Safe" cars (high resale value like Dacia/Toyota), low mileage.
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"      # Willing to buy high-mileage German luxury or less common brands.

class Financials(BaseModel):
    max_budget_mad: float = Field(..., description="Budget in Moroccan Dirhams")
    preferred_payment: str = Field(..., description="Credit, Cash, or Leasing/Mourabaha")
    monthly_limit_mad: Optional[float] = None
    has_down_payment: bool = True # 'Apport initial' is very common in Morocco

class Preferences(BaseModel):
    brands: List[str] = []
    category: Optional[str] = None  # e.g., "Citadine", "SUV", "4x4"
    fuel_type: str = "Diesel"  # Diesel is king in Morocco, default to it
    transmission: str = "Manuelle" # Manual is still very common
    is_imported: Optional[bool] = None # "Dédouanée" vs "Marocaine" (WW)

class User(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    full_name: str
    phone_number: Optional[str]
    city: str = "Casablanca" # Crucial for car location/availability
    
    financials: Financials
    preferences: Preferences
    risk_level: RiskLevel = RiskLevel.MODERATE
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "username": "moustapha_dev",
                "email": "moustapha@omega.ma",
                "full_name": "Moustapha OMEGA",
                "phone_number": "0661234567",
                "city": "Marrakech",
                "financials": {
                    "max_budget_mad": 250000.0,
                    "preferred_payment": "Credit",
                    "monthly_limit_mad": 3500.0,
                    "has_down_payment": True
                },
                "preferences": {
                    "brands": ["Dacia", "Renault", "Hyundai"],
                    "category": "SUV",
                    "fuel_type": "Diesel",
                    "transmission": "Manuelle",
                    "is_imported": False
                },
                "risk_level": "moderate"
            }
        }
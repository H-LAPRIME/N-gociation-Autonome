from pydantic import BaseModel, Field
from typing import List, Optional

class NegotiatedTerms(BaseModel):
    offer_price_mad: float = Field(..., description="The final proposed price in MAD")
    discount_amount_mad: float = Field(0, description="Total discount applied to the market price")
    trade_in_value_mad: Optional[float] = Field(None, description="Value offered for the user's trade-in vehicle")
    monthly_payment_mad: Optional[float] = Field(None, description="Suggested monthly payment if financing")
    payment_method: str = Field(..., description="Recommended payment method (Cash, Financing, Leasing, LLD)")
    
    # Negotiation insights
    persuasion_points: List[str] = Field(default_factory=list, description="Key selling points and persuasion arguments")
    marketing_message: str = Field(..., description="A professional, convincing marketing message for the client")
    
    # Strategy metadata
    leverage_used: str = Field(..., description="The primary leverage factor used (e.g., Stock Urgency, Market Demand)")
    flexibility_level: str = Field(..., description="How much room is left for further negotiation")

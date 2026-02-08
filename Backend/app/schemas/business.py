from pydantic import BaseModel, Field
from typing import List

class BusinessValidation(BaseModel):
    is_approved: bool = Field(..., description="Whether the offer is approved by company policy")
    violations: List[str] = Field(default_factory=list, description="Reason(s) for rejection if any")
    audit_trail: List[str] = Field(default_factory=list, description="Log of checks performed (margin, regulatory, risk)")
    confidence_score: float = Field(..., description="AI's confidence in this validation (0.0 to 1.0)")

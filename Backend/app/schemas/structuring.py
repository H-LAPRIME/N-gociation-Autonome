from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class StructuredOffer(BaseModel):
    contract_id: str = Field(..., description="Unique reference for the legal document")
    final_json: Dict[str, Any] = Field(..., description="Consolidated offer data ready for PDF injection")
    pdf_reference: Optional[str] = Field(None, description="URL or local path to the generated contract document")
    expiry_date: str = Field(..., description="Expiration date of this offer")
    localization: Dict[str, str] = Field(..., description="Locale settings (currency: MAD, etc.)")

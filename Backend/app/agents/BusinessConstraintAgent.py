import json
from typing import Dict, Any
from .base import BaseOmegaAgent
from app.schemas.business import BusinessValidation

class BusinessConstraintAgent(BaseOmegaAgent):
    def __init__(self):
        super().__init__(
            name="BusinessConstraintAgent",
            instructions=[
                "You are the Final Gatekeeper at OMEGA.",
                "Your role is to verify the negotiated offer against OMEGA Business Rules.",
                "CONTEXT: The current year is 2026.",
                "",
                "RULES:",
                "1. MARGIN SAFETY: The discount must NOT exceed 15% of the market average price.",
                "2. REGULATORY: Trade-in vehicles must be from 2010 or newer. 2026 is a VALID year.",
                "3. RISK: If the user is at HIGH risk level, financing is NOT allowed (CASH ONLY).",
                "4. CURRENCY: All amounts must be in MAD.",
                "",
                "HANDLING MISSING DATA:",
                "- CRITICAL: If market_average_price is missing/zero, you CANNOT calculate discount margin.",
                "- ACTION: Log the issue in 'audit_trail' or 'warnings', but DO NOT put it in 'violations'.",
                "- ACTION: Set is_approved: true (Approved with Warning).",
                "- CRITICAL: If trade_in_year is missing, you CANNOT validate age.",
                "- ACTION: Log in 'audit_trail' and set is_approved: true.",
                "",
                "OUTPUT:",
                "Return a JSON object matching the BusinessValidation schema.",
                "Set is_approved: false ONLY if you have actual numbers that violate the limits (e.g. Discount 20% > 15%).",
                "If data is missing, is_approved MUST be true. MISSING DATA IS NOT A VIOLATION."
            ]
        )

    async def validate_final_offer(self, offer_data: Dict[str, Any]) -> BusinessValidation:
        """
        Validates the final negotiated offer against business constraints using pure Python logic.
        OPTIMIZED: No LLM calls - direct validation for 5-8 second speedup.
        """
        violations = []
        audit_trail = []
        warnings = []
        
        # Extract data
        negotiated = offer_data.get('negotiated_terms', {})
        user_profile = offer_data.get('user_profile', {})
        market_data = offer_data.get('market_data', {})
        
        # Get key values
        offer_price = negotiated.get('offer_price_mad', 0)
        discount_amount = negotiated.get('discount_amount_mad', 0)
        market_avg_price = market_data.get('average_price', 0) or market_data.get('market_average_price', 0)
        
        # Enhanced trade-in year lookup (check negotiated terms first, then user profile)
        trade_in_year = negotiated.get('trade_in_year')
        if not trade_in_year:
            # Fallback to user profile extraction structure
            trade_in_info = user_profile.get('trade_in_vehicle_details', {}) or user_profile.get('trade_in', {})
            if isinstance(trade_in_info, dict):
                trade_in_year = trade_in_info.get('year')
        
        payment_method = negotiated.get('payment_method', '').lower()
        risk_level = user_profile.get('risk_level', '').lower()
        
        # RULE 1: Discount Margin Check (max 15%)
        if market_avg_price and market_avg_price > 0:
            discount_percentage = (discount_amount / market_avg_price) * 100
            audit_trail.append(f"Discount Check: {discount_amount:,.2f} MAD / {market_avg_price:,.2f} MAD = {discount_percentage:.2f}%")
            
            if discount_percentage > 15:
                violations.append(f"Discount {discount_percentage:.2f}% exceeds maximum 15% margin")
                audit_trail.append(f"❌ VIOLATION: Discount {discount_percentage:.2f}% > 15%")
            else:
                audit_trail.append(f"✅ PASS: Discount {discount_percentage:.2f}% ≤ 15%")
        else:
            warnings.append("Market average price missing - cannot validate discount margin")
            audit_trail.append("⚠️ WARNING: Market data unavailable for discount validation")
        
        # RULE 2: Trade-in Year Check (must be >= 2010)
        if trade_in_year:
            try:
                year_int = int(trade_in_year)
                audit_trail.append(f"Trade-in Year Check: {year_int}")
                
                if year_int < 2010:
                    violations.append(f"Trade-in vehicle year {year_int} is older than 2010 minimum")
                    audit_trail.append(f"❌ VIOLATION: Year {year_int} < 2010")
                elif year_int > 2026:
                    violations.append(f"Trade-in vehicle year {year_int} is invalid (future year)")
                    audit_trail.append(f"❌ VIOLATION: Year {year_int} > 2026 (current year)")
                else:
                    audit_trail.append(f"✅ PASS: Year {year_int} is valid (2010-2026)")
            except (ValueError, TypeError):
                warnings.append(f"Invalid trade-in year format: {trade_in_year}")
                audit_trail.append(f"⚠️ WARNING: Cannot parse trade-in year '{trade_in_year}'")
        else:
            # No trade-in, skip this check
            audit_trail.append("ℹ️ INFO: No trade-in vehicle - skipping year validation")
        
        # RULE 3: Risk-Based Financing Check (HIGH risk = CASH ONLY)
        if risk_level == 'high' or risk_level == 'élevé':
            audit_trail.append(f"Risk Level Check: {risk_level.upper()}")
            
            if payment_method in ['financing', 'financement', 'credit', 'crédit']:
                violations.append(f"High-risk client cannot use financing - CASH ONLY required")
                audit_trail.append(f"❌ VIOLATION: HIGH risk client using {payment_method}")
            else:
                audit_trail.append(f"✅ PASS: HIGH risk client using {payment_method} (not financing)")
        else:
            audit_trail.append(f"✅ PASS: Risk level '{risk_level}' allows financing")
        
        # RULE 4: Currency Check (must be MAD)
        if offer_price > 0:
            # Assume MAD if price is reasonable for Morocco (10,000 - 10,000,000)
            if 10000 <= offer_price <= 10000000:
                audit_trail.append(f"✅ PASS: Price {offer_price:,.2f} MAD is in valid range")
            else:
                warnings.append(f"Price {offer_price:,.2f} MAD seems unusual - verify currency")
                audit_trail.append(f"⚠️ WARNING: Price {offer_price:,.2f} outside typical range")
        
        # Determine approval
        is_approved = len(violations) == 0
        confidence_score = 1.0 if is_approved else 0.0
        
        # Add summary to audit trail
        if is_approved:
            audit_trail.append(f"✅ FINAL: APPROVED - All business constraints satisfied")
        else:
            audit_trail.append(f"❌ FINAL: REJECTED - {len(violations)} violation(s) found")
        
        if warnings:
            audit_trail.append(f"⚠️ {len(warnings)} warning(s): {'; '.join(warnings)}")
        
        return BusinessValidation(
            is_approved=is_approved,
            violations=violations,
            audit_trail=audit_trail,
            confidence_score=confidence_score
        )


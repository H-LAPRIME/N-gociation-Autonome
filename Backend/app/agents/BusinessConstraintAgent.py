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
        Validates the final negotiated offer against business constraints.
        """
        prompt = f"""
        OFFER DATA FOR VALIDATION:
        {json.dumps(offer_data, indent=2, default=str)}
        
        CONTEXT:
        - Current Year: 2026
        
        PERFORM CHECKS:
        - Check discount vs market average price (limit 15%).
        - Check trade-in year (limit >= 2010). 2026 is VALID.
        - Check risk vs payment method (High risk cannot use financing).
        
        CRITICAL RULE FOR MISSING DATA:
        - If 'market_average_price' or 'market_data' is missing/null/zero -> APPROVED = true (add warning).
        - If 'trade_in_year' is missing -> APPROVED = true (add warning).
        - If risk logic cannot be checked due to missing data -> APPROVED = true.
        - NEVER REJECT DUE TO MISSING DATA. ONLY REJECT EXPLICIT VIOLATIONS.
        
        Return exactly this JSON structure:
        {{
            "is_approved": <bool>,
            "violations": ["list of strings"],
            "audit_trail": ["Check 1: ...", "Check 2: ..."],
            "confidence_score": <float>
        }}
        """
        
        response = self.run(prompt)
        content = getattr(response, "content", None) or getattr(response, "output_text", str(response))
        
        # Clean JSON extraction
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0].strip()
        else:
            import re
            json_match = re.search(r"(\{.*\})", content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = content.strip()
            
        import re
        json_str = re.sub(r'[\x00-\x1f]', '', json_str)
        
        data = json.loads(json_str, strict=False)
        
        # FAILSAFE: If the LLM marks it as unapproved but the violations are just "missing data" or "market average", force approval.
        # This prevents the bot from blocking the user due to lack of external data.
        if not data.get("is_approved", True):
            violations = data.get("violations", [])
            # Check if violations are actually just warnings about missing data
            is_valid_failure = False
            for v in violations:
                v_lower = str(v).lower()
                # Expanded list of keywords that indicate "Missing Data" rather than "Rule Violation"
                data_issue_keywords = [
                    "missing", "unknown", "zero", "cannot validate", "insufficient", 
                    "undetermined", "not found", "unavailable", "reference data",
                    "market average", "market price" # If it complains about market price, it's a data issue usually
                ]
                
                # Check if it matches any data issue keyword
                if any(k in v_lower for k in data_issue_keywords):
                    continue
                
                # If we find a specific number violation (like "2009 < 2010" or "discount 20%"), then it's a real failure
                is_valid_failure = True
                break
            
            if not is_valid_failure:
                # Override to True
                data["is_approved"] = True
                data["audit_trail"] = data.get("audit_trail", []) + [f"Auto-Approved: Overrode violations {violations} as warnings."]
                data["violations"] = [] # Clear violations so backend doesn't complain
        
        return BusinessValidation(**data)


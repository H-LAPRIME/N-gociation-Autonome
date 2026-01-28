from agents.base import BaseOmegaAgent
from tools.bank_api import get_bank_data
from schemas.user import User, RiskLevel, Financials, Preferences, BehavioralAnalysis
from typing import Dict, Any
import json

class UserProfileAgent(BaseOmegaAgent):
    def __init__(self):
        super().__init__(
            name="ClientProfileAgent",
            instructions=[
                "You are an expert Moroccan car-buying consultant and financial analyst.",
                "Extract comprehensive information from user messages including:",
                "- Sentiment (Positive/Neutral/Negative/Frustrated/Excited)",
                "- Urgency level (Low/Medium/High/Critical) with reasoning",
                "- Service preferences (Buy/Rent/Lease/LLD)",
                "- Vehicle preferences (brands, category, fuel type, transmission, usage)",
                "- Budget mentions or constraints",
                "- Location/city mentions",
                "- Contact information if provided",
                "- Specific needs or requirements",
                "Always respond in valid JSON format.",
            ],
            tools=[get_bank_data] 
        )

    async def assess_fiscal_health(self, user_id: int, user_input: str) -> User:
        # 1. Get bank data
        bank_response = await get_bank_data(user_id)
        data = bank_response["data"]

        # 2. Comprehensive AI analysis prompt
        analysis_prompt = f"""
Analyze this user message and extract ALL available information: "{user_input}"

Return a JSON object with the following structure (use null for missing information):
{{
    "sentiment": "Positive/Neutral/Negative/Frustrated/Excited or null",
    "urgency": "Low/Medium/High/Critical or null",
    "urgency_indicators": ["list of phrases indicating urgency"],
    "service_type": "Buy/Rent/Lease/LLD or null",
    "vehicle_category": "SUV/Sedan/Hatchback/Coupe/Pickup/Van or null",
    "brands": ["list of mentioned brands or empty array"],
    "fuel_type": "Diesel/Gasoline/Hybrid/Electric or null",
    "transmission": "Automatic/Manual or null",
    "usage": "Family/Business/City/Off-road/Sport or null",
    "budget_mentioned": "amount in MAD or null",
    "monthly_budget_mentioned": "amount in MAD or null",
    "city": "city name or null",
    "phone_number": "phone number or null",
    "detected_needs": ["list of specific needs mentioned"],
    "flexibility_score": "0.0 to 1.0 based on how flexible user seems, or null"
}}

Examples of urgency indicators: "urgent", "tomorrow", "asap", "quickly", "now", "this week"
Examples of sentiment indicators: complaints, excitement, frustration, satisfaction
Be precise and only extract what is explicitly mentioned or strongly implied.
"""

        # 3. Get AI analysis
        ai_res = await self.agent.arun(analysis_prompt)
        
        # 4. Parse AI response
        ai_data = self._parse_ai_response(ai_res.content)

        # 5. Calculate financial metrics
        income = data.get("monthly_income", 0)
        debts = data.get("monthly_debt_payments", 0)
        bank_seniority = data.get("bank_seniority_months", 0)
        is_blacklisted = data.get("is_blacklisted", False)
        contract_type = data.get("contract_type")
        
        # Calculate DTI (Debt-to-Income ratio)
        dti = (debts / income) if income > 0 else 1.0
        
        # 6. Determine risk level based on multiple factors
        risk_level = self._calculate_risk_level(
            dti=dti,
            is_blacklisted=is_blacklisted,
            contract_type=contract_type,
            bank_seniority=bank_seniority
        )

        # 7. Calculate max budget if not explicitly mentioned
        max_budget = self._calculate_max_budget(
            income=income,
            debts=debts,
            dti=dti,
            mentioned_budget=ai_data.get("budget_mentioned"),
            service_type=ai_data.get("service_type")
        )

        # 8. Calculate monthly limit for rental/lease
        monthly_limit = self._calculate_monthly_limit(
            income=income,
            debts=debts,
            mentioned_monthly=ai_data.get("monthly_budget_mentioned")
        )

        # 9. Determine preferred payment method
        preferred_payment = self._determine_payment_method(
            service_type=ai_data.get("service_type"),
            income=income,
            risk_level=risk_level
        )

        # 10. Build comprehensive user profile
        return User(
            user_id=user_id,
            username=f"user_{user_id}",
            email=f"user_{user_id}@omega.ma",
            full_name="Client OMEGA",
            phone_number=ai_data.get("phone_number"),
            city=ai_data.get("city"),
            income_mad=income,
            risk_level=risk_level,
            financials=Financials(
                max_budget_mad=max_budget,
                preferred_payment=preferred_payment,
                monthly_limit_mad=monthly_limit,
                current_debts_mad=debts,
                is_blacklisted=is_blacklisted,
                contract_type=contract_type,
                bank_seniority_months=bank_seniority
            ),
            preferences=Preferences(
                brands=ai_data.get("brands", []),
                category=ai_data.get("vehicle_category"),
                fuel_type=ai_data.get("fuel_type"),
                transmission=ai_data.get("transmission"),
                usage=ai_data.get("usage")
            ),
            behavior=BehavioralAnalysis(
                sentiment=ai_data.get("sentiment"),
                urgency=ai_data.get("urgency"),
                flexibility=ai_data.get("flexibility_score"),
                detected_needs=ai_data.get("detected_needs", [])
            )
        )

    def _parse_ai_response(self, content: str) -> Dict[str, Any]:
        """Parse AI response and handle JSON extraction"""
        try:
            # Try to extract JSON from markdown code blocks
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()
            
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            # Fallback: return empty dict if parsing fails
            print(f"Failed to parse AI response: {e}")
            return {}

    def _calculate_risk_level(
        self, 
        dti: float, 
        is_blacklisted: bool, 
        contract_type: str, 
        bank_seniority: int
    ) -> RiskLevel:
        """Calculate risk level based on multiple financial factors"""
        if is_blacklisted:
            return RiskLevel.HIGH
        
        # High risk conditions
        if dti >= 0.5 or contract_type not in ["CDI", "Fonctionnaire"]:
            return RiskLevel.HIGH
        
        # Medium risk conditions
        if dti >= 0.35 or bank_seniority < 12:
            return RiskLevel.MEDIUM
        
        # Low risk
        return RiskLevel.LOW

    def _calculate_max_budget(
        self,
        income: float,
        debts: float,
        dti: float,
        mentioned_budget: Any,
        service_type: str
    ) -> float | None:
        """Calculate maximum purchase budget"""
        # If user mentioned a budget, use it
        if mentioned_budget:
            try:
                return float(mentioned_budget)
            except (ValueError, TypeError):
                pass
        
        # Only calculate for purchase (not rental/lease)
        if service_type and service_type.lower() in ["rent", "lease", "lld", "location"]:
            return None
        
        # Calculate available monthly income
        available_monthly = income - debts
        
        # Conservative estimate: 20-30% of available income for 5-7 years
        # Assuming typical Moroccan car loan terms
        if dti < 0.3:
            # Low DTI: can afford 30% monthly payment for 7 years
            monthly_payment = available_monthly * 0.30
            return monthly_payment * 12 * 7  # 7 years
        elif dti < 0.4:
            # Medium DTI: can afford 25% monthly payment for 5 years
            monthly_payment = available_monthly * 0.25
            return monthly_payment * 12 * 5  # 5 years
        else:
            # High DTI: limited budget
            monthly_payment = available_monthly * 0.20
            return monthly_payment * 12 * 5  # 5 years

    def _calculate_monthly_limit(
        self,
        income: float,
        debts: float,
        mentioned_monthly: Any
    ) -> float | None:
        """Calculate maximum monthly payment for rental/lease"""
        # If user mentioned a monthly budget, use it
        if mentioned_monthly:
            try:
                return float(mentioned_monthly)
            except (ValueError, TypeError):
                pass
        
        # Calculate available monthly income
        available_monthly = income - debts
        
        # Conservative: 20-25% of available income for monthly rental
        return available_monthly * 0.25

    def _determine_payment_method(
        self,
        service_type: str,
        income: float,
        risk_level: RiskLevel
    ) -> str | None:
        """Determine preferred payment method"""
        if not service_type:
            return None
        
        service_lower = service_type.lower()
        
        # Map service type to payment method
        if "rent" in service_lower or "louer" in service_lower:
            return "Location"
        elif "lld" in service_lower:
            return "LLD"
        elif "lease" in service_lower or "leasing" in service_lower:
            return "Leasing"
        elif "buy" in service_lower or "achat" in service_lower or "acheter" in service_lower:
            # For purchase, suggest based on financial profile
            if risk_level == RiskLevel.LOW and income >= 15000:
                return "Cash/Financing"
            else:
                return "Financing"
        
        return None
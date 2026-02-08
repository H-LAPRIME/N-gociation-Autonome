from app.agents.base import BaseOmegaAgent
from app.tools.bank_api import get_bank_data
from app.schemas.user import User, RiskLevel, Financials, Preferences, BehavioralAnalysis, TradeInInfo
from typing import Dict, Any
import json

class UserProfileAgent(BaseOmegaAgent):
    """
    Expert Agent for User Profiling & Risk Assessment.
    
    This agent analyzes user messages to extract sentiment, urgency, 
    and vehicle preferences. it also interacts with bank APIs to
    calculate fiscal health (DTI, Risk Level) and determine maximum budget.
    """
    def __init__(self):
        super().__init__(
            name="UserProfileAgent",
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
                "- Trade-in vehicle details (brand, model, year, mileage, condition, accidents, maintenance, owners)",
                "Always respond in valid JSON format.",
            ],
            tools=[get_bank_data] 
        )
        # Detailed Agno configuration
        self.agent.role = "Moroccan Car-Buying Consultant & Financial Analyst"
        self.agent.description = "Expert in extracting and analyzing user profiles for automobile financing and purchasing in Morocco."

    async def assess_fiscal_health(self, user_id: int, user_input: str, current_profile_data: Dict = None) -> User:
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
    "flexibility_score": "0.0 to 1.0 based on how flexible user seems, or null",
    "trade_in": {{
        "brand": "string or null",
        "model": "string or null",
        "year": "integer or null",
        "mileage": "integer or null",
        "condition": "string or null",
        "accidents": "boolean or null",
        "maintenance": "string or null",
        "owners": "integer or null"
    }}
}}

Examples of urgency indicators: "urgent", "tomorrow", "asap", "quickly", "now", "this week"
Examples of sentiment indicators: complaints, excitement, frustration, satisfaction
Be precise and only extract what is explicitly mentioned or strongly implied.
"""

        # 3. Get AI analysis
        ai_res = await self.agent.arun(analysis_prompt)
        
        # 4. Parse AI response
        ai_data = self._parse_ai_response(ai_res.content)
        
        # 4b. MERGE with existing profile data (current_profile_data)
        if current_profile_data:
            # Helper to merge if new is null/empty but old exists
            def text_merge(new, old): return new if new else old
            def list_merge(new, old): return list(set((new or []) + (old or [])))
            
            # Extract previous extraction if available
            prev_extract = current_profile_data.get('profil_extraction', {})
            
            # Merge Top-level fields
            ai_data['city'] = text_merge(ai_data.get('city'), prev_extract.get('city'))
            ai_data['budget_mentioned'] = text_merge(ai_data.get('budget_mentioned'), prev_extract.get('budget_mentioned'))
            
            # Merge vehicle preferences
            prev_prefs = prev_extract.get('vehicle_preferences', {})
            ai_data['vehicle_category'] = text_merge(ai_data.get('vehicle_category'), prev_prefs.get('category'))
            ai_data['brands'] = list_merge(ai_data.get('brands'), prev_prefs.get('brands'))
            
            # Merge Trade-in (Critical for the loop fix)
            prev_trade = prev_extract.get('trade_in_vehicle_details', {})
            new_trade = ai_data.get('trade_in') or {}
            
            merged_trade = {
                "brand": text_merge(new_trade.get('brand'), prev_trade.get('brand')),
                "model": text_merge(new_trade.get('model'), prev_trade.get('model')),
                "year": text_merge(new_trade.get('year'), prev_trade.get('year')),
                "mileage": text_merge(new_trade.get('mileage'), prev_trade.get('mileage')),
                "condition": text_merge(new_trade.get('condition'), prev_trade.get('condition')),
                "accidents": text_merge(new_trade.get('accidents'), prev_trade.get('accidents')),
                "maintenance": text_merge(new_trade.get('maintenance'), prev_trade.get('maintenance')),
                "owners": text_merge(new_trade.get('owners'), prev_trade.get('owners'))
            }
            # Only set trade_in if there is actual data
            if any(merged_trade.values()):
                ai_data['trade_in'] = merged_trade

        # 5. Calculate financial metrics (Prioritize merged profile over mock simulation)
        prev_extract = current_profile_data.get('profil_extraction', {}) if current_profile_data else {}
        
        # Use bank data if valid, otherwise fallback to persisted profile
        income = data.get("monthly_income") or prev_extract.get("monthly_income") or 0
        debts = data.get("monthly_debt_payments") or prev_extract.get("monthly_debt_payments") or 0
        bank_seniority = data.get("bank_seniority_months", 0)
        is_blacklisted = data.get("is_blacklisted", False)
        
        # Priority for contract: Merged extraction > Bank API
        contract_type = prev_extract.get("contract_type") or data.get("contract_type")
        
        # Calculate DTI (Debt-to-Income ratio)
        # If income is 0 or missing, assume 0 DTI (benefit of doubt) instead of 1.0 (high risk)
        dti = (debts / income) if income and income > 0 else 0.0
        
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
            ),
            trade_in=TradeInInfo(**ai_data.get("trade_in", {})) if ai_data.get("trade_in") else None
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
        
        # Helper: Treat missing data leniently for demo purposes
        # If contract_type is missing, assume it's acceptable (don't default to High Risk)
        has_stable_contract = contract_type in ["CDI", "Fonctionnaire"] if contract_type else True 
        
        # High risk conditions (Only if explicit negative signals)
        if dti >= 0.6: # Relaxed DTI threshold
            return RiskLevel.HIGH
        
        if contract_type and not has_stable_contract: # Only penalize if we KNOW it's not stable
            return RiskLevel.HIGH
        
        # Medium risk conditions
        if dti >= 0.40 or bank_seniority < 6: # Relaxed seniority
            return RiskLevel.MEDIUM
        
        # Default to LOW risk for smoother demo experience if no red flags
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
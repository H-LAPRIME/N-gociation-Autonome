"""
User Profile Agent - Fully Database Integrated
"""
from app.agents.base import BaseOmegaAgent
from app.tools.bank_api import get_bank_data
from app.tools.user_service import get_user_complete, merge_user_profile
from app.schemas import User, RiskLevel, Financials, Preferences, BehavioralAnalysis, TradeInInfo
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)


class UserProfileAgent(BaseOmegaAgent):
    """
    Expert Agent for User Profiling & Risk Assessment.
    Fully integrated with database - reads existing data and saves updates.
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
            tools=[] 
        )
        self.agent.role = "Moroccan Car-Buying Consultant & Financial Analyst"
        self.agent.description = "Expert in extracting and analyzing user profiles for automobile financing and purchasing in Morocco."

    async def assess_fiscal_health(
        self, 
        user_id: int, 
        user_input: str, 
        db: AsyncSession
    ) -> Optional[User]:
        """
        Main method: Analyze user input, merge with existing profile, calculate financials, save to DB
        
        Args:
            user_id: User ID
            user_input: User's message to analyze
            db: Database session
            
        Returns:
            Updated User profile or None if error
        """
        try:
            logger.info(f"🔍 Analyzing profile for user {user_id}")
            
            # Step 1: Get existing user profile from DB
            existing_profile = await get_user_complete(user_id, db)
            
            if not existing_profile:
                logger.error(f"❌ User {user_id} not found in database")
                return None
            
            # Step 2: Get bank/financial data from DB
            bank_response = await get_bank_data(user_id, db)
            
            if bank_response["status"] != "success":
                logger.warning(f"⚠️ Could not get bank data for user {user_id}")
                bank_data = {}
            else:
                bank_data = bank_response["data"]
            
            # Step 3: Extract new information from user input using AI
            ai_extracted = await self._extract_from_input(user_input, existing_profile)
            
            # Step 4: Build new profile data from AI extraction
            new_profile = self._build_profile_from_extraction(
                user_id=user_id,
                existing=existing_profile,
                ai_data=ai_extracted,
                bank_data=bank_data
            )
            
            # Step 5: Merge new profile with existing (smart merge)
            merged_profile = await merge_user_profile(user_id, new_profile, db)
            
            if not merged_profile:
                logger.error(f"❌ Failed to merge profile for user {user_id}")
                return None
            
            logger.info(f"✅ Profile updated successfully for user {user_id}")
            return merged_profile
            
        except Exception as e:
            logger.error(f"❌ Error in assess_fiscal_health: {e}", exc_info=True)
            return None

    async def _extract_from_input(self, user_input: str, existing_profile: User) -> Dict[str, Any]:
        """
        Use AI to extract information from user message
        """
        analysis_prompt = f"""
Analyze this user message and extract ALL available information: "{user_input}"

Current user profile context:
- City: {existing_profile.city or "Unknown"}
- Preferences: {existing_profile.preferences.dict() if existing_profile.preferences else "None"}
- Trade-in: {existing_profile.trade_in.dict() if existing_profile.trade_in else "None"}

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

        try:
            ai_res = await self.agent.arun(analysis_prompt)
            return self._parse_ai_response(ai_res.content)
        except Exception as e:
            logger.error(f"❌ AI extraction failed: {e}")
            return {}

    def _build_profile_from_extraction(
        self, 
        user_id: int,
        existing: User,
        ai_data: Dict[str, Any],
        bank_data: Dict[str, Any]
    ) -> User:
        """
        Build complete user profile from AI extraction + bank data + calculations
        """
        # Get financial metrics from bank data (with fallbacks)
        income = bank_data.get("monthly_income") or existing.income_mad or 0
        debts = bank_data.get("monthly_debt_payments") or (existing.financials.current_debts_mad if existing.financials else 0)
        bank_seniority = bank_data.get("bank_seniority_months") or (existing.financials.bank_seniority_months if existing.financials else 0)
        is_blacklisted = bank_data.get("is_blacklisted") or (existing.financials.is_blacklisted if existing.financials else False)
        contract_type = bank_data.get("contract_type") or (existing.financials.contract_type if existing.financials else None)
        
        # Calculate DTI
        dti = (debts / income) if income and income > 0 else 0.0
        
        # Calculate risk level
        risk_level = self._calculate_risk_level(
            dti=dti,
            is_blacklisted=is_blacklisted,
            contract_type=contract_type,
            bank_seniority=bank_seniority
        )
        
        # Calculate max budget
        max_budget = self._calculate_max_budget(
            income=income,
            debts=debts,
            dti=dti,
            mentioned_budget=ai_data.get("budget_mentioned"),
            service_type=ai_data.get("service_type")
        )
        
        # Calculate monthly limit
        monthly_limit = self._calculate_monthly_limit(
            income=income,
            debts=debts,
            mentioned_monthly=ai_data.get("monthly_budget_mentioned")
        )
        
        # Determine payment method
        preferred_payment = self._determine_payment_method(
            service_type=ai_data.get("service_type"),
            income=income,
            risk_level=risk_level
        )
        
        # Build complete profile
        return User(
            user_id=user_id,
            username=existing.username,
            email=existing.email,
            full_name=existing.full_name,
            phone_number=ai_data.get("phone_number") or existing.phone_number,
            city=ai_data.get("city") or existing.city,
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
            trade_in=TradeInInfo(**ai_data.get("trade_in", {})) if ai_data.get("trade_in") and any(ai_data.get("trade_in", {}).values()) else None
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
            logger.error(f"❌ Failed to parse AI response: {e}")
            return {}

    def _calculate_risk_level(
        self, 
        dti: float, 
        is_blacklisted: bool, 
        contract_type: Optional[str], 
        bank_seniority: int
    ) -> RiskLevel:
        """Calculate risk level based on multiple financial factors"""
        if is_blacklisted:
            return RiskLevel.HIGH
        
        # High risk conditions
        if dti >= 0.6:
            return RiskLevel.HIGH
        
        if contract_type and contract_type not in ["CDI", "Fonctionnaire"]:
            return RiskLevel.HIGH
        
        # Medium risk conditions
        if dti >= 0.40 or bank_seniority < 6:
            return RiskLevel.MEDIUM
        
        # Default to LOW risk
        return RiskLevel.LOW

    def _calculate_max_budget(
        self,
        income: float,
        debts: float,
        dti: float,
        mentioned_budget: Any,
        service_type: Optional[str]
    ) -> Optional[float]:
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
        
        # Conservative estimate
        if dti < 0.3:
            monthly_payment = available_monthly * 0.30
            return monthly_payment * 12 * 7  # 7 years
        elif dti < 0.4:
            monthly_payment = available_monthly * 0.25
            return monthly_payment * 12 * 5  # 5 years
        else:
            monthly_payment = available_monthly * 0.20
            return monthly_payment * 12 * 5  # 5 years

    def _calculate_monthly_limit(
        self,
        income: float,
        debts: float,
        mentioned_monthly: Any
    ) -> Optional[float]:
        """Calculate maximum monthly payment for rental/lease"""
        if mentioned_monthly:
            try:
                return float(mentioned_monthly)
            except (ValueError, TypeError):
                pass
        
        available_monthly = income - debts
        return available_monthly * 0.25

    def _determine_payment_method(
        self,
        service_type: Optional[str],
        income: float,
        risk_level: RiskLevel
    ) -> Optional[str]:
        """Determine preferred payment method"""
        if not service_type:
            return None
        
        service_lower = service_type.lower()
        
        if "rent" in service_lower or "louer" in service_lower:
            return "Location"
        elif "lld" in service_lower:
            return "LLD"
        elif "lease" in service_lower or "leasing" in service_lower:
            return "Leasing"
        elif "buy" in service_lower or "achat" in service_lower or "acheter" in service_lower:
            if risk_level == RiskLevel.LOW and income >= 15000:
                return "Cash/Financing"
            else:
                return "Financing"
        
        return None
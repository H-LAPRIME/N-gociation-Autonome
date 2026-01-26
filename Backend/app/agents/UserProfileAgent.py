# Moustapha: User Profile Agent

# Responsibility: Authenticate user, assess fiscal health, and determine risk profile.
# Tools: bank_api.py
# Tasks:
# 1. Define Pydantic schema for user profile (income, credit score, current debts).
# 2. Implement risk_assessment() method to calculate debt-to-income ratio.
# 3. Output should be a RiskProfile object (Low, Medium, High).

from app.agents.base import BaseOmegaAgent
from app.tools.bank_api import get_bank_data
from app.schemas.user import User, RiskLevel, Financials, Preferences

class UserProfileAgent(BaseOmegaAgent):
    def __init__(self):
        super().__init__(
            name="ClientProfileAgent",
            instructions=[
                "Analyze the user's deep profile for car negotiation.",
                "1. Use 'get_bank_data' to fetch financial status.",
                "2. Calculate Taux d'endettement (Debt/Income).",
                "3. Assess risk: HIGH if blacklisted, DTI > 40%, or Freelance/CDD without seniority.",
                "4. Identify car preferences and intended usage (e.g., family, professional).",
                "Ensure the output is a perfectly structured User object."
            ],
            tools=[get_bank_data] 
        )

    async def assess_fiscal_health(self, user_id: int, user_input: str) -> User:
        # 1. Fetch data using the tool
        bank_response = await get_bank_data(user_id)
        data = bank_response["data"]

        # 2. Logic to determine risk level based on constraints
        income = data.get("monthly_income", 0)
        debts = data.get("monthly_debt_payments", 0)
        dti = debts / income if income > 0 else 1.0
        
        if data.get("is_blacklisted") or dti > 0.4:
            final_risk = RiskLevel.HIGH
        elif dti > 0.2:
            final_risk = RiskLevel.MEDIUM
        else:
            final_risk = RiskLevel.LOW

        # 3. Construct the User object (In Phase 2, LLM will fill Preferences from user_input)
        return User(
            user_id=user_id,
            username=f"user_{user_id}",
            email=f"user_{user_id}@omega.ma",
            full_name="Fetched Name",
            income_mad=income,
            risk_level=final_risk,
            financials=Financials(
                max_budget_mad=income * 10, # Mock budget logic
                preferred_payment="Credit" if dti < 0.3 else "Cash",
                current_debts_mad=debts,
                is_blacklisted=data.get("is_blacklisted", False),
                contract_type=data.get("contract_type", "Unknown")
            ),
            preferences=Preferences(
                usage="Daily Commute", # Task 6.1.2: Identify usage
                brands=["Dacia"]
            )
        )
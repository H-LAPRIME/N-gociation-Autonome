# Moustapha: User Profile Agent

# Responsibility: Authenticate user, assess fiscal health, and determine risk profile.
# Tools: bank_api.py
# Tasks:
# 1. Define Pydantic schema for user profile (income, credit score, current debts).
# 2. Implement risk_assessment() method to calculate debt-to-income ratio.
# 3. Output should be a RiskProfile object (Low, Medium, High).

from app.agents.base import BaseOmegaAgent

class UserProfileAgent(BaseOmegaAgent):
    def __init__(self):
        super().__init__(
            name="ProfileAgent",
            instructions=[""]
        )

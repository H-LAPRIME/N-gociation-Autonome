"""
Models package - imports all models for easy access
"""
from app.models.user import User
from app.models.user_financials import UserFinancials

# Export all models
__all__ = ["User", "UserFinancials"]
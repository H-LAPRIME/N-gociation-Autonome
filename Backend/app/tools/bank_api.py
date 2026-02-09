"""
Bank Service - Database Integration
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User, UserFinancials
from typing import Dict
import logging

logger = logging.getLogger(__name__)


async def get_bank_data(user_id: int, db: AsyncSession) -> Dict:
    """
    Gets user financial data from database
    
    Args:
        user_id: The user's ID
        db: Async database session
    
    Returns:
        Dictionary with status and user financial data
    """
    try:
        # Query user
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"User {user_id} not found in bank service")
            return {
                "status": "error",
                "message": "User not found",
                "data": None
            }
        
        # Get financials
        result = await db.execute(
            select(UserFinancials).where(UserFinancials.user_id == user_id)
        )
        financials = result.scalar_one_or_none()
        
        # Build response data
        bank_data = {
            "monthly_income": user.income_mad or 0,
            "monthly_debt_payments": financials.current_debts_mad if financials else 0,
            "is_blacklisted": financials.is_blacklisted if financials else False,
            "contract_type": financials.contract_type if financials else None,
            "bank_seniority_months": financials.bank_seniority_months if financials else 0,
            "max_budget_mad": financials.max_budget_mad if financials else None,
            "preferred_payment": financials.preferred_payment if financials else None,
            "monthly_limit_mad": financials.monthly_limit_mad if financials else None,
        }
        
        logger.info(f"✅ Bank data retrieved for user {user_id}")
        return {
            "status": "success",
            "data": bank_data
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting bank data for user {user_id}: {e}")
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }
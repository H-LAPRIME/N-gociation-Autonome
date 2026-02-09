"""
User Service - Complete CRUD operations for User and Financials
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User, UserFinancials
from app.schemas import User as UserSchema, Financials, Preferences, BehavioralAnalysis, TradeInInfo, RiskLevel
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


async def get_user_complete(user_id: int, db: AsyncSession) -> Optional[UserSchema]:
    """
    Get complete user profile with all relationships
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        UserSchema object or None if not found
    """
    try:
        # Get user
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"User {user_id} not found")
            return None
        
        # Get financials
        result = await db.execute(
            select(UserFinancials).where(UserFinancials.user_id == user_id)
        )
        financials = result.scalar_one_or_none()
        
        # Build Pydantic schema
        user_data = UserSchema(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            phone_number=user.phone_number,
            city=user.city,
            income_mad=user.income_mad,
            risk_level=user.risk_level,
            financials=Financials(**{
                "max_budget_mad": financials.max_budget_mad,
                "preferred_payment": financials.preferred_payment,
                "monthly_limit_mad": financials.monthly_limit_mad,
                "current_debts_mad": financials.current_debts_mad,
                "is_blacklisted": financials.is_blacklisted,
                "contract_type": financials.contract_type,
                "bank_seniority_months": financials.bank_seniority_months,
            }) if financials else None,
            preferences=Preferences(**user.preferences) if user.preferences else None,
            behavior=BehavioralAnalysis(**user.behavior) if user.behavior else None,
            trade_in=TradeInInfo(**user.trade_in) if user.trade_in else None,
        )
        
        return user_data
        
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return None


async def update_user_profile(user_id: int, profile_data: UserSchema, db: AsyncSession) -> bool:
    """
    Update user profile with all nested data
    
    Args:
        user_id: User ID
        profile_data: Complete user profile data
        db: Database session
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get existing user
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.error(f"User {user_id} not found for update")
            return False
        
        # Update user fields
        user.username = profile_data.username
        user.email = profile_data.email
        user.full_name = profile_data.full_name
        user.phone_number = profile_data.phone_number
        user.city = profile_data.city
        user.income_mad = profile_data.income_mad
        user.risk_level = profile_data.risk_level
        
        # Update JSON fields
        user.preferences = profile_data.preferences.dict() if profile_data.preferences else {}
        user.behavior = profile_data.behavior.dict() if profile_data.behavior else {}
        user.trade_in = profile_data.trade_in.dict() if profile_data.trade_in else {}
        
        # Update or create financials
        if profile_data.financials:
            result = await db.execute(
                select(UserFinancials).where(UserFinancials.user_id == user_id)
            )
            financials = result.scalar_one_or_none()
            
            if financials:
                # Update existing
                financials.max_budget_mad = profile_data.financials.max_budget_mad
                financials.preferred_payment = profile_data.financials.preferred_payment
                financials.monthly_limit_mad = profile_data.financials.monthly_limit_mad
                financials.current_debts_mad = profile_data.financials.current_debts_mad
                financials.is_blacklisted = profile_data.financials.is_blacklisted
                financials.contract_type = profile_data.financials.contract_type
                financials.bank_seniority_months = profile_data.financials.bank_seniority_months
            else:
                # Create new
                new_financials = UserFinancials(
                    user_id=user_id,
                    max_budget_mad=profile_data.financials.max_budget_mad,
                    preferred_payment=profile_data.financials.preferred_payment,
                    monthly_limit_mad=profile_data.financials.monthly_limit_mad,
                    current_debts_mad=profile_data.financials.current_debts_mad,
                    is_blacklisted=profile_data.financials.is_blacklisted,
                    contract_type=profile_data.financials.contract_type,
                    bank_seniority_months=profile_data.financials.bank_seniority_months,
                )
                db.add(new_financials)
        
        await db.commit()
        logger.info(f"✅ User {user_id} profile updated successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating user {user_id}: {e}")
        await db.rollback()
        return False


async def merge_user_profile(user_id: int, new_data: UserSchema, db: AsyncSession) -> Optional[UserSchema]:
    """
    Intelligently merge new profile data with existing data
    Only updates fields that have new non-null values
    
    Args:
        user_id: User ID
        new_data: New profile data to merge
        db: Database session
        
    Returns:
        Updated UserSchema or None
    """
    try:
        # Get existing profile
        existing = await get_user_complete(user_id, db)
        
        if not existing:
            logger.error(f"Cannot merge - user {user_id} not found")
            return None
        
        # Helper function to merge values (prefer new if not None)
        def merge_value(new, old):
            return new if new is not None else old
        
        # Helper for lists (combine and deduplicate)
        def merge_list(new, old):
            if not new:
                return old or []
            if not old:
                return new or []
            return list(set(new + old))
        
        # Merge top-level fields
        merged = UserSchema(
            user_id=user_id,
            username=existing.username,  # Don't change username/email
            email=existing.email,
            full_name=merge_value(new_data.full_name, existing.full_name),
            phone_number=merge_value(new_data.phone_number, existing.phone_number),
            city=merge_value(new_data.city, existing.city),
            income_mad=merge_value(new_data.income_mad, existing.income_mad),
            risk_level=merge_value(new_data.risk_level, existing.risk_level),
        )
        
        # Merge financials
        if new_data.financials or existing.financials:
            new_fin = new_data.financials
            old_fin = existing.financials
            
            merged.financials = Financials(
                max_budget_mad=merge_value(new_fin.max_budget_mad if new_fin else None, old_fin.max_budget_mad if old_fin else None),
                preferred_payment=merge_value(new_fin.preferred_payment if new_fin else None, old_fin.preferred_payment if old_fin else None),
                monthly_limit_mad=merge_value(new_fin.monthly_limit_mad if new_fin else None, old_fin.monthly_limit_mad if old_fin else None),
                current_debts_mad=merge_value(new_fin.current_debts_mad if new_fin else None, old_fin.current_debts_mad if old_fin else None),
                is_blacklisted=merge_value(new_fin.is_blacklisted if new_fin else None, old_fin.is_blacklisted if old_fin else None),
                contract_type=merge_value(new_fin.contract_type if new_fin else None, old_fin.contract_type if old_fin else None),
                bank_seniority_months=merge_value(new_fin.bank_seniority_months if new_fin else None, old_fin.bank_seniority_months if old_fin else None),
            )
        
        # Merge preferences
        if new_data.preferences or existing.preferences:
            new_pref = new_data.preferences
            old_pref = existing.preferences
            
            merged.preferences = Preferences(
                brands=merge_list(new_pref.brands if new_pref else None, old_pref.brands if old_pref else None),
                category=merge_value(new_pref.category if new_pref else None, old_pref.category if old_pref else None),
                fuel_type=merge_value(new_pref.fuel_type if new_pref else None, old_pref.fuel_type if old_pref else None),
                transmission=merge_value(new_pref.transmission if new_pref else None, old_pref.transmission if old_pref else None),
                usage=merge_value(new_pref.usage if new_pref else None, old_pref.usage if old_pref else None),
            )
        
        # Merge behavior
        if new_data.behavior or existing.behavior:
            new_beh = new_data.behavior
            old_beh = existing.behavior
            
            merged.behavior = BehavioralAnalysis(
                sentiment=merge_value(new_beh.sentiment if new_beh else None, old_beh.sentiment if old_beh else None),
                urgency=merge_value(new_beh.urgency if new_beh else None, old_beh.urgency if old_beh else None),
                flexibility=merge_value(new_beh.flexibility if new_beh else None, old_beh.flexibility if old_beh else None),
                detected_needs=merge_list(new_beh.detected_needs if new_beh else None, old_beh.detected_needs if old_beh else None),
            )
        
        # Merge trade-in
        if new_data.trade_in or existing.trade_in:
            new_trade = new_data.trade_in
            old_trade = existing.trade_in
            
            merged.trade_in = TradeInInfo(
                brand=merge_value(new_trade.brand if new_trade else None, old_trade.brand if old_trade else None),
                model=merge_value(new_trade.model if new_trade else None, old_trade.model if old_trade else None),
                year=merge_value(new_trade.year if new_trade else None, old_trade.year if old_trade else None),
                mileage=merge_value(new_trade.mileage if new_trade else None, old_trade.mileage if old_trade else None),
                condition=merge_value(new_trade.condition if new_trade else None, old_trade.condition if old_trade else None),
                accidents=merge_value(new_trade.accidents if new_trade else None, old_trade.accidents if old_trade else None),
                maintenance=merge_value(new_trade.maintenance if new_trade else None, old_trade.maintenance if old_trade else None),
                owners=merge_value(new_trade.owners if new_trade else None, old_trade.owners if old_trade else None),
            )
        
        # Save merged profile
        success = await update_user_profile(user_id, merged, db)
        
        if success:
            return merged
        else:
            return None
            
    except Exception as e:
        logger.error(f"❌ Error merging user profile: {e}")
        return None
"""
UserFinancials Model
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db_config import Base

class UserFinancials(Base):
    __tablename__ = "user_financials"
    
    # Primary key and foreign key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Financial fields
    max_budget_mad = Column(Float, nullable=True)
    preferred_payment = Column(String, nullable=True)
    monthly_limit_mad = Column(Float, nullable=True)
    current_debts_mad = Column(Float, nullable=True)
    is_blacklisted = Column(Boolean, nullable=True, default=False)
    contract_type = Column(String, nullable=True)
    bank_seniority_months = Column(Integer, nullable=True)
    
    # Relationship back to user
    user = relationship("User", back_populates="financials")
    
    def __repr__(self):
        return f"<UserFinancials(user_id={self.user_id}, max_budget={self.max_budget_mad})>"
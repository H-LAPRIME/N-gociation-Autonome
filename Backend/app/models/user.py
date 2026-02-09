"""
User Model
"""
from sqlalchemy import Column, Integer, String, Float, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db_config import Base
import enum

class RiskLevelEnum(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class User(Base):
    __tablename__ = "users"
    
    # Primary fields
    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    city = Column(String, nullable=True)
    income_mad = Column(Float, nullable=False, default=0.0)
    
    # Risk level
    risk_level = Column(SQLEnum(RiskLevelEnum), nullable=True)
    
    # JSON fields for nested data
    preferences = Column(JSON, nullable=True, default={})
    behavior = Column(JSON, nullable=True, default={})
    trade_in = Column(JSON, nullable=True, default={})
    
    # Relationship to financials (one-to-one)
    financials = relationship("UserFinancials", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, email={self.email}, username={self.username})>"
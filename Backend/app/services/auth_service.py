import hashlib
import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from app.models import User, UserFinancials
from app.schemas.user import UserCreate, UserLogin
from app.db_config import get_async_db
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("JWT_SECRET", "supersecret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 43200))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_user_by_email(email: str, db: AsyncSession) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def get_user_by_id(user_id: int, db: AsyncSession) -> Optional[User]:
    result = await db.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()

async def create_user(user_in: UserCreate, db: AsyncSession) -> User:
    if await get_user_by_email(user_in.email, db):
        raise ValueError("Email already registered")
    
    new_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hash_password(user_in.password),
        username=user_in.email.split("@")[0],
        city=user_in.city,
        income_mad=user_in.income_mad or 0.0,
        preferences=user_in.preferences.model_dump() if user_in.preferences else {},
        behavior={},
        trade_in={}
    )
    
    db.add(new_user)
    await db.flush() # Genterate user_id
    
    if user_in.financials:
        financials = UserFinancials(
            user_id=new_user.user_id,
            max_budget_mad=user_in.financials.max_budget_mad,
            preferred_payment=user_in.financials.preferred_payment,
            monthly_limit_mad=user_in.financials.monthly_limit_mad,
            current_debts_mad=user_in.financials.current_debts_mad,
            is_blacklisted=user_in.financials.is_blacklisted,
            contract_type=user_in.financials.contract_type,
            bank_seniority_months=user_in.financials.bank_seniority_months,
        )
        db.add(financials)
    
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def authenticate_user(user_in: UserLogin, db: AsyncSession) -> Optional[User]:
    user = await get_user_by_email(user_in.email, db)
    if not user:
        return None
    if not verify_password(user_in.password, user.hashed_password):
        return None
    return user

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            raise credentials_exception
        user_id = int(user_id_raw)
    except (jwt.PyJWTError, ValueError, TypeError) as e:
        logger.error(f"JWT error: {str(e)}")
        raise credentials_exception
    
    user = await get_user_by_id(user_id, db)
    if user is None:
        raise credentials_exception
        
    # Return as dict for compatibility with existing code
    return {
        "user_id": user.user_id,
        "email": user.email,
        "full_name": user.full_name,
        "username": user.username,
        "city": user.city,
        "income_mad": user.income_mad
    }

async def update_user(user_id: int, update_data: Dict, db: AsyncSession) -> User:
    user = await get_user_by_id(user_id, db)
    if not user:
        raise ValueError("User not found")
        
    for key, value in update_data.items():
        if hasattr(user, key) and key not in ["user_id", "email", "hashed_password"]:
            setattr(user, key, value)
            
    await db.commit()
    await db.refresh(user)
    return user


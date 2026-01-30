import json
import os
import hashlib
import jwt
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from app.schemas.user import UserCreate, UserLogin
from dotenv import load_dotenv
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "users.json")
SECRET_KEY = os.getenv("JWT_SECRET", "supersecret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 43200))

def _load_users() -> List[Dict]:
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def _save_users(users: List[Dict]):
    # Ensure directory exists
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=4)

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

def get_user_by_email(email: str) -> Optional[Dict]:
    users = _load_users()
    for user in users:
        if user["email"] == email:
            return user
    return None

def get_user_by_id(user_id: int) -> Optional[Dict]:
    users = _load_users()
    for user in users:
        if user["user_id"] == user_id:
            return user
    return None

def create_user(user_in: UserCreate) -> Dict:
    users = _load_users()
    if get_user_by_email(user_in.email):
        raise ValueError("Email already registered")
    
    new_user = {
        "user_id": len(users) + 1,
        "email": user_in.email,
        "full_name": user_in.full_name,
        "hashed_password": hash_password(user_in.password),
        "username": user_in.email.split("@")[0],
        "city": user_in.city,
        "income_mad": user_in.income_mad,
        "financials": user_in.financials.model_dump() if user_in.financials else {},
        "preferences": user_in.preferences.model_dump() if user_in.preferences else {},
        "trade_in": None
    }
    
    users.append(new_user)
    _save_users(users)
    return new_user

def authenticate_user(user_in: UserLogin) -> Optional[Dict]:
    user = get_user_by_email(user_in.email)
    if not user:
        return None
    if not verify_password(user_in.password, user["hashed_password"]):
        return None
    return user


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def update_user(user_id: int, update_data: Dict) -> Dict:
    users = _load_users()
    for i, user in enumerate(users):
        if user["user_id"] == user_id:
            # Update fields selectively
            for key, value in update_data.items():
                if key in ["full_name", "city", "income_mad", "financials", "preferences", "trade_in"]:
                    users[i][key] = value
            _save_users(users)
            return users[i]
    raise ValueError("User not found")

async def get_current_user(token: str = Depends(oauth2_scheme)):
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
        print(f"DEBUG auth error: {str(e)}")
        raise credentials_exception
    
    user = get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user


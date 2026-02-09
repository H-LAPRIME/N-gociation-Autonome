"""
OMEGA API - Main Entry Point
----------------------------
This file initializes the FastAPI application, configures CORS,
mounts static folders, and registers all API routes for the OMEGA project.
"""
from dotenv import load_dotenv
import os
from typing import List, Dict, Optional
from datetime import datetime
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from app.schemas import User, AnalyzeProfileRequest, UserLogin, UserCreate
from app.agents.UserProfileAgent import UserProfileAgent
from app.agents.MarketAnalysisAgent import MarketAnalysisAgent
from app.agents.OrchestratorAgent import OrchestratorAgent
from app.services import auth_service
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="OMEGA Backend")

# --- MIDDLEWARE & ROUTERS --- 

# Configure CORS (Cross-Origin Resource Sharing)
# In production, specific origins should be white-listed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register high-level API routers
from app.api.negotiation import router as negotiation_router
from app.api.chat import router as chat_router
from app.api.v1.api import router as api_v1_router

app.include_router(negotiation_router)
app.include_router(chat_router)
app.include_router(api_v1_router, prefix="/v1")

from fastapi.staticfiles import StaticFiles

# Create directory if not exists
os.makedirs("data/contracts", exist_ok=True)
# Mount static files for contracts
app.mount("/contracts", StaticFiles(directory="data/contracts"), name="contracts")

from app.services.auth_service import get_current_user
from app.db_config import get_async_db
from app.tools.user_service import get_user_complete

# --- ROOT ENDPOINT ---

@app.get("/")
async def root():
    """Welcome endpoint to check API availability."""
    return {"message": "Bienvenue sur l'API OMEGA"}

# --- AUTHENTICATION ENDPOINTS ---

@app.post("/auth/signup")
async def signup(user: UserCreate):
    """Register a new user and return an access token."""
    try:
        new_user = auth_service.create_user(user)
        access_token = auth_service.create_access_token(data={"sub": new_user["user_id"]})
        return {
            "success": True, 
            "message": "User created successfully", 
            "access_token": access_token, 
            "token_type": "bearer",
            "user": {k: v for k, v in new_user.items() if k != "hashed_password"}
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login")
async def login(user: UserLogin):
    authenticated_user = auth_service.authenticate_user(user)
    if not authenticated_user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = auth_service.create_access_token(data={"sub": authenticated_user["user_id"]})
    return {
        "success": True, 
        "message": "Login successful", 
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {k: v for k, v in authenticated_user.items() if k != "hashed_password"}
    }

@app.get("/user/profile")
async def get_user_profile(
    current_user: Dict = Depends(get_current_user),
    db = Depends(get_async_db)
):
    """Get complete user profile from PostgreSQL database."""
    try:
        user_data = await get_user_complete(current_user["user_id"], db)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found in database")
        return user_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/user/profile")
async def update_user_profile(
    user_update: Dict, 
    current_user: Dict = Depends(get_current_user),
    db = Depends(get_async_db)
):
    """Update user profile in PostgreSQL database."""
    try:
        from app.tools.user_service import update_user_profile as update_profile_service
        from app.schemas import User as UserSchema, Financials, Preferences, BehavioralAnalysis, TradeInInfo
        
        # Convert dict to UserSchema
        profile_data = UserSchema(
            user_id=current_user["user_id"],
            username=current_user.get("username", ""),
            email=current_user.get("email", ""),
            full_name=current_user.get("full_name", ""),
            phone_number=user_update.get("phone_number"),
            city=user_update.get("city"),
            income_mad=user_update.get("income_mad", 0),
            risk_level=user_update.get("risk_level"),
            financials=Financials(**user_update.get("financials", {})) if user_update.get("financials") else None,
            preferences=Preferences(**user_update.get("preferences", {})) if user_update.get("preferences") else None,
            behavior=BehavioralAnalysis(**user_update.get("behavior", {})) if user_update.get("behavior") else None,
            trade_in=TradeInInfo(**user_update.get("trade_in", {})) if user_update.get("trade_in") else None,
        )
        
        success = await update_profile_service(current_user["user_id"], profile_data, db)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update user profile")
        
        # Return updated profile
        updated_user = await get_user_complete(current_user["user_id"], db)
        return {"success": True, "user": updated_user}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

user_profile_agent = UserProfileAgent()
@app.post("/user/analyze")
async def analyze_user_profile(request: AnalyzeProfileRequest, current_user: Dict = Depends(get_current_user)):
    try:
        result = await user_profile_agent.assess_fiscal_health(
            user_id=current_user["user_id"],
            user_input=request.user_input
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class OrchestrateRequest(BaseModel):
    query: str
    history: List[Dict[str, str]] = []
    user_profile_state: Dict = {}
    session_id: Optional[str] = None

# --- ORCHESTRATION & AGENTS --- 

# Orchestrator handles the complex multi-agent flows
orchestrator = OrchestratorAgent()

@app.post("/orchestrate")
async def orchestrate_flow(request: OrchestrateRequest, current_user: Dict = Depends(get_current_user)):
    """
    Main orchestration endpoint.
    Coordinates between multiple agents to handle car transaction queries.
    """
    import logging
    import traceback
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"📥 Orchestrate request from user {current_user['user_id']}: {request.query[:100]}")
        
        result = await orchestrator.coordinate(
            user_id=current_user["user_id"],
            user_query=request.query,
            history=request.history,
            user_profile_state=request.user_profile_state,
            session_id=request.session_id
        )
        
        logger.info(f"📤 Orchestrate response status: {result.get('status', 'unknown')}")
        return result
    except Exception as e:
        # Log full traceback for debugging
        logger.error(f"❌ ERROR in /orchestrate endpoint:")
        logger.error(f"Exception: {str(e)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # En développement, on active le reload
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)



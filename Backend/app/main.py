# Point d'entrée principal de l'application FastAPI OMEGA (Responsabilité: Moustapha).
# Ce fichier initialise l'application, configure les middlewares (CORS, etc.)
# et inclut les routes de l'API (api/v1/api.py).
from dotenv import load_dotenv
import os
load_dotenv()

from fastapi import FastAPI, HTTPException
# from app.api.v1 import api_router
from app.schemas import User, AnalyzeProfileRequest
from app.agents.UserProfileAgent import UserProfileAgent
from app.agents.MarketAnalysisAgent import MarketAnalysisAgent

app = FastAPI(title="OMEGA Backend")

# app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Bienvenue sur l'API OMEGA"}

@app.get("/user/profile")
async def get_user_profile():
    return User(
        user_id=1,
        username="johndoe",
        email="john.doe@example.com",
        full_name="John Doe"
    )

user_profile_agent = UserProfileAgent()
@app.post("/user/analyze")
async def analyze_user_profile(request: AnalyzeProfileRequest):
    try:
        result = await user_profile_agent.assess_fiscal_health(
            user_id=request.user_id,
            user_input=request.user_input
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


market_agent = MarketAnalysisAgent()
@app.get("/market/trends")
async def market_trends(model: str):
    result = await market_agent.analyze_market(model)
    return {"result": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# Point d'entrée principal de l'application FastAPI OMEGA (Responsabilité: Moustapha).
# Ce fichier initialise l'application, configure les middlewares (CORS, etc.)
# et inclut les routes de l'API (api/v1/api.py).

from fastapi import FastAPI
# from app.api.v1 import api_router
from schemas import User

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
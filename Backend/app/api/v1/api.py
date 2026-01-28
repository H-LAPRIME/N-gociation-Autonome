from fastapi import APIRouter
from .valuation import router as valuation_router


api_router = APIRouter()

api_router.include_router(valuation_router, prefix="/valuation", tags=["Valuation"])


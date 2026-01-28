# app/api/v1/valuation.py
from fastapi import APIRouter
from app.agents.ValuationAgent import ValuationAgent
from app.schemas.valuation import CarInput, ValuationOutput

router = APIRouter()

def get_agent():
    return ValuationAgent()  

@router.post("/", response_model=ValuationOutput)
def estimate_car(car: CarInput):
    agent = get_agent()
    return agent.appraise_vehicle(car.dict())

import asyncio
import json
from app.agents.NegotiationAgent import NegotiationAgent
from dotenv import load_dotenv

load_dotenv()

async def test_negotiation():
    agent = NegotiationAgent()
    
    # Mock data
    user_data = {
        "user_id": 1,
        "income_mad": 25000,
        "risk_level": "Low",
        "financials": {
            "max_budget_mad": 450000,
            "preferred_payment": "Financing"
        },
        "preferences": {
            "brands": ["Peugeot"],
            "category": "SUV"
        },
        "behavior": {
            "sentiment": "Excited",
            "urgency": "High",
            "flexibility": 0.8
        }
    }
    
    valuation_data = {
        "state": 4,
        "price_range": {
            "min": 120000,
            "max": 135000
        }
    }
    
    market_data = {
        "target_model": "3008",
        "target_brand": "Peugeot",
        "inventory": {
            "stock_available": 12,
            "stock_level": "moyen",
            "avg_market_price": 380000
        },
        "market_trends": {
            "demand_level": "élevée",
            "price_pressure": "stable"
        },
        "strategic_insights": {
            "negotiation_position": "position forte",
            "price_flexibility": "modérée (5-8% de remise envisageable)"
        }
    }
    
    print("--- Starting Negotiation ---")
    result = await agent.negotiate(user_data, valuation_data, market_data)
    
    print("\n[NEGOTIATED OFFER]")
    output = json.dumps(result.model_dump(), indent=2, ensure_ascii=True) # ensure_ascii=True is safer for console
    print(output)
    
    assert result.offer_price_mad > 0
    assert result.marketing_message != ""
    print("\nVerification successful!")


if __name__ == "__main__":
    asyncio.run(test_negotiation())

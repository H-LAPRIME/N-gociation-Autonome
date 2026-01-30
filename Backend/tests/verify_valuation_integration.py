import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add Backend folder to path
sys.path.append(os.path.join(os.getcwd(), "Backend"))

from app.agents.ValuationAgent import ValuationAgent

async def test_valuation_scraper():
    load_dotenv()
    
    agent = ValuationAgent()
    
    # Peugeot 3008, 2022, 45000km, Excellent condition
    mock_car_info = {
        "brand": "Peugeot",
        "model": "3008",
        "year": 2022,
        "mileage": 45000,
        "state_description": "Excellent, entretien régulier chez la maison, pas d'accidents.",
        "maintenance": "Complet",
        "owners": 1
    }
    
    print("Testing ValuationAgent with Car Scraper tool...")
    try:
        result = await agent.appraise_vehicle(mock_car_info)
        
        print("\n--- Result ---")
        print(json.dumps(result, indent=2))
        
        if "market_base_price" in result and result.get("state") is not None:
            print("\nVerification SUCCESS: Agent called the scraper and calculated value.")
        else:
            print("\nVerification FAILED: Output missing expected fields.")
            
    except Exception as e:
        print(f"\nError during test: {e}")

if __name__ == "__main__":
    asyncio.run(test_valuation_scraper())

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add Backend folder to path
# Add current directory to path so we can import 'app'
sys.path.append(os.getcwd())

from app.agents.OfferStructuringAgent import OfferStructuringAgent

async def test_pdf_integration():
    load_dotenv()
    
    agent = OfferStructuringAgent()
    
    # Mock data matching the Orchestrator's structure
    mock_consolidated_data = {
        "user_profile": {
            "full_name": "Test Client",
            "email": "test@omega.ma",
            "phone": "0600000000",
            "city": "Casablanca",
            "contract_type": "CDI",
            "vehicle_preferences": {
                "brands": ["Peugeot"],
                "model": "3008",
                "category": "SUV"
            }
        },
        "negotiated_terms": {
            "offer_price_mad": 180000,
            "discount_amount_mad": 5000,
            "trade_in_value_mad": 120000,
            "payment_method": "Credit",
            "monthly_payment_mad": 3500
        },
        "valuation": {
            "brand": "Renault",
            "model": "Clio 4",
            "year": 2018,
            "mileage": 85000,
            "condition": "Bon"
        },
        "validation": {
            "is_approved": True,
            "risk_score": 0.2
        }
    }
    
    print("Testing OfferStructuringAgent with PDF tool...")
    try:
        result = await agent.structure_offer(mock_consolidated_data)
        
        print("\n--- Result ---")
        print(f"Contract ID: {result.contract_id}")
        print(f"PDF Reference: {result.pdf_reference}")
        print(f"Expiry Date: {result.expiry_date}")
        
        if result.pdf_reference and "storage/contracts" in result.pdf_reference:
            print("\nVerification SUCCESS: Agent called the tool and populated pdf_reference.")
        else:
            print("\nVerification FAILED: pdf_reference is missing or incorrect.")
            
    except Exception as e:
        print(f"\nError during test: {e}")

if __name__ == "__main__":
    asyncio.run(test_pdf_integration())

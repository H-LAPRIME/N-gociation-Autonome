import asyncio
import os
import json
from app.agents.OrchestratorAgent import OrchestratorAgent
from dotenv import load_dotenv

load_dotenv()

async def test_orchestrator():
    orchestrator = OrchestratorAgent()
    
    # Test case: User wants a Peugeot 3008 and has a Dacia Duster to trade in
    user_id = 1
    user_query = "Je veux acheter une Peugeot 3008. J'ai une Dacia Duster de 2018 avec 50000 km en excellent état à reprendre."
    
    print(f"--- Sending query: {user_query} ---")
    
    try:
        result = await orchestrator.coordinate(user_id, user_query)
        
        print("\n--- Orchestration Result ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Basic assertions
        assert result["user_profile"] is not None
        assert "Peugeot" in str(result["user_profile"]["preferences"]["brands"])
        
        if result["valuation"]:
            print("\n✅ Valuation successful")
        else:
            print("\n⚠️ Valuation missing (check if agent extracted trade-in info correctly)")
            
        if result.get("negotiated_offer"):
            print("\n✅ Negotiation successful")
        else:
            print("\n⚠️ Negotiation missing")
            
    except Exception as e:
        print(f"\n❌ Error during orchestration: {e}")

        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_orchestrator())

import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging
from app.agents.UserProfileAgent import UserProfileAgent
from app.db_config import AsyncSessionLocal
from app.tools.user_service import get_user_complete

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_profile_agent():
    """Test UserProfileAgent - extract info and update DB"""
    
    agent = UserProfileAgent()
    
    print("\n" + "="*70)
    print("🤖 TESTING USER PROFILE AGENT")
    print("="*70)
    
    # Test with User 4 (empty profile - best for testing extraction)
    user_id = 4
    user_input = "Bonjour, j'habite à Tanger. Je cherche une Toyota Yaris automatique. Mon budget est de 200000 MAD maximum. J'ai besoin d'une voiture pour aller au travail tous les jours."
    
    print(f"\n📝 User Input:")
    print(f"   {user_input}")
    
    async with AsyncSessionLocal() as db:
        try:
            # Get profile BEFORE agent updates it
            print(f"\n📋 BEFORE Agent Analysis:")
            before = await get_user_complete(user_id, db)
            if before:
                print(f"   City: {before.city}")
                print(f"   Phone: {before.phone_number}")
                print(f"   Risk Level: {before.risk_level}")
                print(f"   Preferences: {before.preferences}")
                print(f"   Max Budget: {before.financials.max_budget_mad if before.financials else None}")
            
            # Run the agent
            print(f"\n🤖 Running Agent Analysis...")
            result = await agent.assess_fiscal_health(
                user_id=user_id,
                user_input=user_input,
                db=db
            )
            
            if result:
                print(f"\n✅ AFTER Agent Analysis:")
                print(f"   City: {result.city}")
                print(f"   Phone: {result.phone_number}")
                print(f"   Risk Level: {result.risk_level}")
                
                if result.preferences:
                    print(f"\n   🚗 Preferences:")
                    print(f"      Brands: {result.preferences.brands}")
                    print(f"      Category: {result.preferences.category}")
                    print(f"      Transmission: {result.preferences.transmission}")
                    print(f"      Usage: {result.preferences.usage}")
                
                if result.financials:
                    print(f"\n   💰 Financials:")
                    print(f"      Max Budget: {result.financials.max_budget_mad} MAD")
                    print(f"      Preferred Payment: {result.financials.preferred_payment}")
                    print(f"      Contract: {result.financials.contract_type}")
                
                if result.behavior:
                    print(f"\n   🎭 Behavior:")
                    print(f"      Sentiment: {result.behavior.sentiment}")
                    print(f"      Urgency: {result.behavior.urgency}")
                
                # Verify it was saved to DB
                print(f"\n🔍 Verifying DB Update...")
                updated = await get_user_complete(user_id, db)
                if updated:
                    print(f"   ✅ Data persisted to database!")
                    print(f"   City in DB: {updated.city}")
                    print(f"   Brands in DB: {updated.preferences.brands if updated.preferences else None}")
                else:
                    print(f"   ❌ Data NOT found in DB")
                
                print(f"\n✅ TEST PASSED!")
            else:
                print(f"\n❌ Agent returned no result")
                
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            logger.error("Test failed:", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_profile_agent())
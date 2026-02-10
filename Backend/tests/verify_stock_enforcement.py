import asyncio
import os
import json
import logging
from app.agents.OrchestratorAgent import OrchestratorAgent
from dotenv import load_dotenv
from sqlalchemy import select
from app.db_config import get_async_db
from app.models import User, UserFinancials

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_test_user():
    """Ensure test user exists in the DB"""
    async for db in get_async_db():
        result = await db.execute(select(User).where(User.user_id == 1))
        user = result.scalar_one_or_none()
        if not user:
            logger.info("🔨 Creating test user 1 in database...")
            test_user = User(
                user_id=1,
                username="testuser",
                email="test@example.com",
                hashed_password="hashed_password",
                full_name="Test User",
                income_mad=12000.0,
                city="Rabat"
            )
            db.add(test_user)
            await db.commit()
            
            # Add financials
            financials = UserFinancials(
                user_id=1,
                max_budget_mad=200000.0,
                contract_type="CDI"
            )
            db.add(financials)
            await db.commit()
            logger.info("✅ Test user created")
        break

async def verify_stock_logic():
    await create_test_user()
    orchestrator = OrchestratorAgent()
    user_id = 1
    
    # Case 1: Out of Stock (Clio 4)
    print("\n--- TEST 1: Out of Stock (Clio 4) ---")
    query_out = "[AUTO_NEGOTIATE] Client veut acheter une Renault Clio 4."
    res_out = await orchestrator.coordinate(user_id, query_out)
    print(f"DEBUG: Case 1 returned")
    print(f"Intent: {res_out.get('intent')}")
    print(f"Response: {res_out.get('chat_response')}")
    
    # Case 2: In Stock (Polo)
    print("\n--- TEST 2: In Stock (Polo) ---")
    query_in = "[AUTO_NEGOTIATE] Client veut acheter une Volkswagen Polo."
    print(f"DEBUG: Starting Case 2...")
    res_in = await orchestrator.coordinate(user_id, query_in)
    print(f"DEBUG: Case 2 returned")
    print(f"Intent: {res_in.get('intent')}")
    print(f"Has Offer: {'negotiated_offer' in res_in or 'ui_action' in res_in}")
    if res_in.get('chat_response'):
        print(f"Response snippet: {res_in.get('chat_response')[:100]}...")

if __name__ == "__main__":
    asyncio.run(verify_stock_logic())

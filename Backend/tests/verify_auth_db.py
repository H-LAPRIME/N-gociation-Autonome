import asyncio
import sys
import os

# Add Backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import auth_service
from app.db_config import get_async_db
from app.schemas.user import UserCreate, UserLogin
from sqlalchemy import text

async def verify_auth():
    print("🚀 Starting Auth DB Verification...")
    
    test_email = "test_auth_db@example.com"
    test_pass = "password123"
    
    async for db in get_async_db():
        # 1. Clean up existing test user if any
        print("🧹 Cleaning up old test data...")
        await db.execute(text("DELETE FROM users WHERE email = :email"), {"email": test_email})
        await db.commit()
        
        # 2. Test Signup
        print("📝 Testing Signup...")
        try:
            signup_data = UserCreate(
                email=test_email,
                password=test_pass,
                full_name="Auth DB Tester",
                city="Marrakech",
                income_mad=15000,
                financials={"max_budget_mad": 250000, "contract_type": "CDI"}
            )
            new_user = await auth_service.create_user(signup_data, db)
            print(f"✅ Signup successful: ID={new_user.user_id}, Name={new_user.full_name}")
        except Exception as e:
            print(f"❌ Signup failed: {e}")
            return
            
        # 3. Test Login
        print("🔑 Testing Login...")
        try:
            login_data = UserLogin(email=test_email, password=test_pass)
            user = await auth_service.authenticate_user(login_data, db)
            if user:
                print(f"✅ Login successful: Hello {user.full_name}")
                token = auth_service.create_access_token(data={"sub": user.user_id})
                print(f"✅ Token generated: {token[:20]}...")
            else:
                print("❌ Login failed: Invalid credentials")
                return
        except Exception as e:
            print(f"❌ Login error: {e}")
            return
            
        # 4. Verify password hashing
        print("🛡️ Verifying security...")
        if user.hashed_password == test_pass:
            print("❌ SECURITY FAILURE: Password stored in plain text!")
        else:
            print("✅ Security check passed: Password is hashed.")

        # 5. Test Profile Update
        print("📝 Testing Profile Update...")
        try:
            update_data = {"phone_number": "0600000000", "city": "Casablanca"}
            updated_user = await auth_service.update_user(user.user_id, update_data, db)
            if updated_user.phone_number == "0600000000" and updated_user.city == "Casablanca":
                print(f"✅ Profile update successful: {updated_user.city}, {updated_user.phone_number}")
            else:
                print(f"❌ Profile update failed: {updated_user.city}, {updated_user.phone_number}")
                return
        except Exception as e:
            print(f"❌ Profile update error: {e}")
            return

        print("\n✨ Auth DB Verification Complete!")
        break

if __name__ == "__main__":
    asyncio.run(verify_auth())

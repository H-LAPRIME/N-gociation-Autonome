"""
Test script for the interactive negotiation system
Run this after starting the backend server
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Test credentials (use existing user or create one)
TEST_USER = {
    "email": "test@omega.com",
    "password": "test123"
}

def login():
    """Login and get auth token"""
    response = requests.post(f"{BASE_URL}/auth/login", json=TEST_USER)
    if response.status_code == 200:
        data = response.json()
        print("✅ Login successful")
        return data['access_token']
    else:
        print(f"❌ Login failed: {response.text}")
        print("\n📝 Creating new user...")
        # Try to create user
        signup_data = {
            **TEST_USER,
            "full_name": "Test User",
            "phone": "0612345678",
            "city": "Casablanca",
            "monthly_income": 15000,
            "contract_type": "CDI"
        }
        response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
        if response.status_code == 200:
            data = response.json()
            print("✅ Signup successful")
            return data['access_token']
        else:
            print(f"❌ Signup failed: {response.text}")
            return None

def test_start_negotiation(token):
    """Test starting a negotiation session"""
    print("\n🚀 Testing: Start Negotiation")
    
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "user_id": 1,
        "initial_offer_data": {
            "user_profile": {
                "full_name": "Ahmed Benali",
                "email": "ahmed@example.com",
                "city": "Casablanca",
                "monthly_income": 15000,
                "contract_type": "CDI",
                "vehicle_preferences": {
                    "brands": ["Renault"],
                    "model": "Clio",
                    "category": "Citadine"
                }
            },
            "valuation": {
                "brand": "Dacia",
                "model": "Duster",
                "year": 2020,
                "mileage": 45000,
                "condition": "Bon"
            },
            "market_data": {
                "average_price": 250000,
                "market_trend": "stable"
            }
        },
        "max_rounds": 5
    }
    
    response = requests.post(f"{BASE_URL}/negotiation/start", json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Session created: {result['session_id']}")
        print(f"📊 Round: {result['round']}/{result['round'] + result['remaining_rounds']}")
        print(f"💬 Agent: {result['agent_response'][:100]}...")
        print(f"💰 Offer: {result['revised_offer']['offer_price_mad']} MAD")
        return result['session_id']
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return None

def test_counter_offer(token, session_id):
    """Test sending a counter-offer"""
    print("\n🔄 Testing: Counter-Offer")
    
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "message": "Je voudrais un prix de 240000 MAD avec des mensualités de 4000 MAD",
        "counter_offer": {
            "desired_price": 240000,
            "desired_monthly": 4000
        },
        "action": "counter"
    }
    
    response = requests.post(
        f"{BASE_URL}/negotiation/{session_id}/message",
        json=data,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Counter-offer processed")
        print(f"📊 Round: {result['round']}/{result['round'] + result['remaining_rounds']}")
        print(f"💬 Agent: {result['agent_response'][:100]}...")
        if result.get('revised_offer'):
            print(f"💰 New Offer: {result['revised_offer']['offer_price_mad']} MAD")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False

def test_get_history(token, session_id):
    """Test getting conversation history"""
    print("\n📜 Testing: Get History")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/negotiation/{session_id}/history",
        headers=headers
    )
    
    if response.status_code == 200:
        history = response.json()
        print(f"✅ Retrieved {len(history)} messages")
        for msg in history:
            speaker_icon = "🤖" if msg['speaker'] == 'agent' else "👤"
            print(f"  {speaker_icon} Round {msg['round_number']}: {msg['message'][:50]}...")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False

def test_accept_offer(token, session_id):
    """Test accepting an offer"""
    print("\n✅ Testing: Accept Offer")
    
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "message": "J'accepte cette offre",
        "action": "accept"
    }
    
    response = requests.post(
        f"{BASE_URL}/negotiation/{session_id}/message",
        json=data,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Offer accepted!")
        print(f"📄 Status: {result['status']}")
        print(f"💬 Agent: {result['agent_response']}")
        
        if result.get('revised_offer', {}).get('contract_id'):
            print(f"📋 Contract ID: {result['revised_offer']['contract_id']}")
            print(f"📄 PDF: {result['revised_offer'].get('pdf_reference', 'N/A')}")
        
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 OMEGA Negotiation System - Test Suite")
    print("=" * 60)
    
    # Login
    token = login()
    if not token:
        print("\n❌ Cannot proceed without authentication")
        return
    
    # Start negotiation
    session_id = test_start_negotiation(token)
    if not session_id:
        print("\n❌ Cannot proceed without session")
        return
    
    # Send counter-offer
    if not test_counter_offer(token, session_id):
        print("\n⚠️ Counter-offer failed, but continuing...")
    
    # Get history
    if not test_get_history(token, session_id):
        print("\n⚠️ History retrieval failed, but continuing...")
    
    # Accept offer (this will trigger PDF generation)
    test_accept_offer(token, session_id)
    
    print("\n" + "=" * 60)
    print("✅ Test Suite Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()

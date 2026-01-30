import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agents.BusinessConstraintAgent import BusinessConstraintAgent

async def test_trade_in_year_fix():
    print("\n🔍 VERIFYING TRADE-IN YEAR FIX...")
    agent = BusinessConstraintAgent()
    
    # Scenario: Trade-in year is MISSING from negotiated terms but present in user profile
    # Value: 2007 (should be a violation since it's < 2010)
    test_data = {
        'negotiated_terms': {
            'offer_price_mad': 150000,
            'discount_amount_mad': 10000,
            'payment_method': 'cash',
            # 'trade_in_year' is missing HERE!
        },
        'user_profile': {
            'trade_in': {
                'year': 2007  # But it's available HERE
            }
        },
        'market_data': {
            'average_price': 160000
        }
    }
    
    print("\nRunning validation with 2007 trade-in year (in profile only)...")
    result = await agent.validate_final_offer(test_data)
    
    # Verification
    has_trade_in_violation = any("2007" in v and "2010" in v for v in result.violations)
    
    if not result.is_approved and has_trade_in_violation:
        print("✅ SUCCESS: 2007 trade-in year was correctly detected as a violation!")
    else:
        print("❌ FAILURE: Bug still exists or validation logic failed.")
        print(f"   Approved: {result.is_approved}")
        print(f"   Violations: {result.violations}")
    
    # Scenario: Valid year
    test_data_valid = {
        'negotiated_terms': {
            'offer_price_mad': 150000,
            'discount_amount_mad': 10000,
            'payment_method': 'cash',
            'trade_in_year': 2015  # Explicitly present and valid
        },
        'user_profile': {},
        'market_data': {
            'average_price': 160000
        }
    }
    
    print("\nRunning validation with 2015 trade-in year (valid)...")
    result_valid = await agent.validate_final_offer(test_data_valid)
    if result_valid.is_approved:
        print("✅ SUCCESS: 2015 trade-in year was correctly approved!")
    else:
        print("❌ FAILURE: 2015 trade-in year was incorrectly rejected.")

if __name__ == "__main__":
    asyncio.run(test_trade_in_year_fix())

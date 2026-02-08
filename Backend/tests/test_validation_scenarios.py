"""
Test Scenarios for Business Validation
Demonstrates ✅ PASS, ❌ VIOLATION, and ⚠️ WARNING cases
"""
import asyncio
import sys
sys.path.insert(0, 'c:\\Users\\pc\\Desktop\\OMEGA\\backend')

from app.agents.BusinessConstraintAgent import BusinessConstraintAgent

async def run_scenarios():
    agent = BusinessConstraintAgent()
    
    print("=" * 80)
    print("SCENARIO 1: ✅ PASS - Valid Offer (All Rules Satisfied)")
    print("=" * 80)
    scenario_1 = {
        'negotiated_terms': {
            'offer_price_mad': 150000,
            'discount_amount_mad': 20000,  # 11.76% discount (< 15%)
            'payment_method': 'cash',
            'trade_in_year': 2018,  # Valid year (>= 2010)
            'trade_in_value_mad': 50000
        },
        'user_profile': {
            'risk_level': 'low',
            'full_name': 'Ahmed Benali',
            'email': 'ahmed@example.com'
        },
        'market_data': {
            'average_price': 170000
        }
    }
    
    result_1 = await agent.validate_final_offer(scenario_1)
    print(f"\n🎯 Result: {'✅ APPROVED' if result_1.is_approved else '❌ REJECTED'}")
    print(f"📊 Confidence: {result_1.confidence_score}")
    print(f"🚫 Violations: {result_1.violations}")
    print("\n📋 Audit Trail:")
    for item in result_1.audit_trail:
        print(f"   {item}")
    
    print("\n\n" + "=" * 80)
    print("SCENARIO 2: ❌ VIOLATION - Excessive Discount & Old Trade-in")
    print("=" * 80)
    scenario_2 = {
        'negotiated_terms': {
            'offer_price_mad': 120000,
            'discount_amount_mad': 35000,  # 20.59% discount (> 15% VIOLATION!)
            'payment_method': 'financing',
            'trade_in_year': 2008,  # Too old (< 2010 VIOLATION!)
            'trade_in_value_mad': 30000
        },
        'user_profile': {
            'risk_level': 'medium',
            'full_name': 'Fatima Zahra',
            'email': 'fatima@example.com'
        },
        'market_data': {
            'average_price': 170000
        }
    }
    
    result_2 = await agent.validate_final_offer(scenario_2)
    print(f"\n🎯 Result: {'✅ APPROVED' if result_2.is_approved else '❌ REJECTED'}")
    print(f"📊 Confidence: {result_2.confidence_score}")
    print(f"🚫 Violations: {result_2.violations}")
    print("\n📋 Audit Trail:")
    for item in result_2.audit_trail:
        print(f"   {item}")
    
    print("\n\n" + "=" * 80)
    print("SCENARIO 3: ⚠️ WARNING - Missing Market Data (Approved with Warning)")
    print("=" * 80)
    scenario_3 = {
        'negotiated_terms': {
            'offer_price_mad': 180000,
            'discount_amount_mad': 25000,
            'payment_method': 'cash',
            'trade_in_value_mad': None  # No trade-in
        },
        'user_profile': {
            'risk_level': 'low',
            'full_name': 'Youssef Alami',
            'email': 'youssef@example.com'
        },
        'market_data': {}  # Missing market data - WARNING!
    }
    
    result_3 = await agent.validate_final_offer(scenario_3)
    print(f"\n🎯 Result: {'✅ APPROVED' if result_3.is_approved else '❌ REJECTED'}")
    print(f"📊 Confidence: {result_3.confidence_score}")
    print(f"🚫 Violations: {result_3.violations}")
    print("\n📋 Audit Trail:")
    for item in result_3.audit_trail:
        print(f"   {item}")
    
    print("\n\n" + "=" * 80)
    print("BONUS SCENARIO: ❌ VIOLATION - High Risk Client Using Financing")
    print("=" * 80)
    scenario_4 = {
        'negotiated_terms': {
            'offer_price_mad': 200000,
            'discount_amount_mad': 15000,  # 8.82% discount (OK)
            'payment_method': 'financing',  # VIOLATION! High risk must use CASH
            'trade_in_value_mad': None
        },
        'user_profile': {
            'risk_level': 'high',  # HIGH RISK!
            'full_name': 'Karim Idrissi',
            'email': 'karim@example.com'
        },
        'market_data': {
            'average_price': 170000
        }
    }
    
    result_4 = await agent.validate_final_offer(scenario_4)
    print(f"\n🎯 Result: {'✅ APPROVED' if result_4.is_approved else '❌ REJECTED'}")
    print(f"📊 Confidence: {result_4.confidence_score}")
    print(f"🚫 Violations: {result_4.violations}")
    print("\n📋 Audit Trail:")
    for item in result_4.audit_trail:
        print(f"   {item}")
    
    print("\n\n" + "=" * 80)
    print("✅ All scenarios completed!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_scenarios())

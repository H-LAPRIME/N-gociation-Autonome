# Outil de simulation d'API bancaire (Responsabilité: Moustapha).
# Ce module gère les connexions aux services financiers pour :
# 1. Vérifier l'historique bancaire de l'utilisateur.
# 2. Calculer sa capacité de remboursement.
# 3. Récupérer un score de solvabilité (Mocké en Phase 1).

async def get_bank_data(user_id: str):
    mock_db = {
        1: {
            "monthly_income": 12000,
            "monthly_debt_payments": 3000,
            "is_blacklisted": False,
            "contract_type": "CDI", 
            "bank_seniority_months": 24
        },
        2: {
            "monthly_income": 6000,
            "monthly_debt_payments": 3500,
            "is_blacklisted": True,
            "contract_type": "CDD", # Hard to get credit with CDD
            "bank_seniority_months": 6
        }
    }
    
    user_data = mock_db.get(user_id, {
        "monthly_income": 0,
        "monthly_debt_payments": 0,
        "is_blacklisted": False,
        "contract_type": "Freelance",
        "bank_seniority_months": 0
    })
    
    return {"status": "success", "data": user_data}
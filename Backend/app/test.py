from .agents.ValuationAgent import ValuationAgent

def test_agent():
    agent = ValuationAgent()

    car_json = {
        "brand_model": "Dacia Sandero",
        "year": 2018,
        "mileage_km": 60000,
        "condition": "Moyen",
        "maintenance_history": {
            "service_book": "Complet",
            "accident": "Non",
            "owners": 1
        }
    }

    result = agent.appraise_vehicle(car_json)
    print("Résultat brut de l’agent :")
    print(result)


if __name__ == "__main__":
    test_agent()

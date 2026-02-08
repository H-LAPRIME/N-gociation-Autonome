# Reda: Vehicle State Agent (Rule-Based)
# Responsibility: Evaluate the global condition of a vehicle (state 1–5) using predefined rules
# Output: JSON { "state": int }

import json
from .base import BaseOmegaAgent
from datetime import datetime


class ValuationAgent(BaseOmegaAgent):
    """
    Rule-Based Agent for Vehicle Condition Evaluation (État).
    
    Evaluates the global condition of a vehicle based on rules.
    Returns a state score between 1 (very poor) and 5 (excellent).
    """

    def __init__(self):
        super().__init__(
            name="VehicleStateAgent",
            instructions=[
                "Évaluation de l’état global d’un véhicule selon règles prédéfinies.",
                "Entrée : JSON avec année, kilométrage, accidents, entretien, nombre de propriétaires.",
                "Retourne un score d’état entier entre 1 (très mauvais) et 5 (excellent).",
                "Retourne STRICTEMENT un JSON valide.",
                "Aucun texte, aucune explication."
            ]
        )

    def appraise_vehicle(self, car_json: dict) -> dict:
        """
        Rule-based evaluation of vehicle condition.
        
        Input example:
        {
            "year": 2018,
            "mileage": 45000,
            "accidents": 1,
            "maintenance": "regular",  # "regular", "irregular", "poor"
            "owners": 1
        }
        
        Output example:
        { "state": 4 }
        """

        # Default state
        state = 5

        # --- Rule 1: Age ---
        current_year = datetime.now().year
        age = current_year - car_json.get("year", current_year)
        if age > 15:
            state -= 2
        elif age > 10:
            state -= 1

        # --- Rule 2: Mileage ---
        mileage = car_json.get("mileage", 0)
        if mileage > 200_000:
            state -= 2
        elif mileage > 150_000:
            state -= 1
        elif mileage > 100_000:
            state -= 0  # neutral
        elif mileage < 20_000:
            state += 1

        # --- Rule 3: Accidents ---
        accidents = car_json.get("accidents", 0)
        if accidents >= 3:
            state -= 2
        elif accidents == 2:
            state -= 1
        elif accidents == 1:
            state -= 0  # minor effect

        # --- Rule 4: Maintenance ---
        maintenance = car_json.get("maintenance", "regular").lower()
        if maintenance == "poor":
            state -= 2
        elif maintenance == "irregular":
            state -= 1

        # --- Rule 5: Number of Owners ---
        owners = car_json.get("owners", 1)
        if owners > 3:
            state -= 2
        elif owners == 3:
            state -= 1

        # Clamp state between 1 and 5
        state = max(1, min(5, state))

        return {"state": state}

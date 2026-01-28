# Reda: Valuation Agent

# Responsibility: Accurately estimate the value of the trade-in vehicle.
# Tools: car_scraper.py
# Tasks:
# 1. Implement appraise_vehicle() to fetch market data using car_scraper.
# 2. Add logic to adjust price based on mileage, age, and maintenance history.
# 3. Output a precise ValuationReport with min/max suggested price.

import re
from .base import BaseOmegaAgent
import json

class ValuationAgent(BaseOmegaAgent):
    def __init__(self):
        super().__init__(
            name="ValuationAgent",
            instructions=[
                "Tu es un agent d’estimation de prix de voitures d’occasion au Maroc.",
                "Tu reçois un JSON décrivant une voiture.",
                "N’utilise PAS les tendances du marché ni des sources externes.",
                "Utilise uniquement : année, kilométrage, état, accidents, entretien, nombre de propriétaires.",
                "Étape 1 : Déduis un état global entre 1 (mauvais) et 5 (excellent).",
                "Étape 2 : Applique un coefficient logique et conservateur basé sur cet état.",
                "Étape 3 : Calcule un prix estimé en dirhams marocains.",
                "Étape 4 : Fournis une fourchette de prix (±10%).",
                "Retourne UNIQUEMENT un JSON valide, sans texte explicatif."
            ]
        )
    
    def extract_json(self, text: str) -> str:
        """
        Extrait un JSON depuis un bloc Markdown ```json ... ```
        ou retourne le texte tel quel s'il est déjà brut.
        """
        text = text.strip()

        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            return match.group(1).strip()

        return text
    
    def appraise_vehicle(self, car_json: dict) -> dict:
        """
        Reçoit un JSON voiture et retourne une fourchette de prix.
        Synchrone maintenant.
        """
        # self.run n'est plus async
        response = self.run(f"""
            JSON ENTRÉE :
            {json.dumps(car_json)}

            FORMAT DE SORTIE EXACT :
            {{
            "state": <1-5>,
            "price_range": {{
                "min": <number>,
                "max": <number>
            }}
            }}
            """)

        content = getattr(response, "content", None) or getattr(response, "output_text", None)

        if not content:
            return {"error": "Réponse vide"}

        clean_json = self.extract_json(content)

        try:
            return json.loads(clean_json)
        except json.JSONDecodeError:
            return {
                "error": "JSON invalide après nettoyage",
                "raw_content": content
            }
        
    
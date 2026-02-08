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
from app.tools.car_scraper import get_vehicle_estimation

class ValuationAgent(BaseOmegaAgent):
    """
    Agent for Vehicle Appraisal & Valuation.
    
    This agent estimates the market value of trade-in vehicles using
    web scraping techniques and adjust the price based on condition,
    mileage, and age.
    """
    def __init__(self):
        super().__init__(
            name="ValuationAgent",
            instructions=[
                "Tu es un agent d’estimation de prix de voitures d’occasion au Maroc.",
                "Tu reçois un JSON décrivant une voiture.",
                "ÉTAPE 1 : Utilise l'outil 'get_vehicle_estimation' pour obtenir une base de prix du marché (Argus).",
                "ÉTAPE 2 : Analyse les détails du véhicule (année, kilométrage, état, accidents, entretien).",
                "ÉTAPE 3 : Ajuste le prix du marché en fonction de l'état global (1 mauvais - 5 excellent) et des autres facteurs.",
                "ÉTAPE 4 : Calcule un prix final en dirhams marocains (MAD).",
                "ÉTAPE 5 : Fournis une fourchette de prix (±10%).",
                "Retourne UNIQUEMENT un JSON valide correspondant au format demandé."
            ],
            tools=[get_vehicle_estimation]
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
    
    async def appraise_vehicle(self, car_json: dict) -> dict:
        """
        Reçoit un JSON voiture et retourne une fourchette de prix.
        Direct execution via Python (No LLM for speed).
        """
        brand = car_json.get("brand", "Unknown")
        model = car_json.get("model", "Unknown")
        year = car_json.get("year", 2020)
        mileage = car_json.get("mileage", 0)
        condition = car_json.get("condition", "Bon")
        
        # 1. Get base market price from scraper
        estimation = await get_vehicle_estimation(model, year, mileage)
        base_price = estimation.get("estimated_price", 0)
        
        # 2. Apply condition adjustment (Pure Python logic)
        condition_map = {
            "Excellent": 1.10,
            "Bon": 1.0,
            "Moyen": 0.90,
            "Mauvais": 0.80,
            "Non roulant": 0.50
        }
        # Fuzzy max matching for condition string
        factor = 1.0
        for k, v in condition_map.items():
            if k.lower() in str(condition).lower():
                factor = v
                break
                
        adjusted_price = base_price * factor
        
        # 3. Calculate range (±10%)
        price_min = round(adjusted_price * 0.9, -2)
        price_max = round(adjusted_price * 1.1, -2)
        
        # 4. Determine state score (1-5)
        state_score = int(factor * 4) + 1 # Rough mapping: 0.5->3, 0.8->4, 1.0->5. Adjustable.
        state_score = min(max(state_score, 1), 5)

        return {
            "state": state_score,
            "market_base_price": base_price,
            "price_range": {
                "min": price_min,
                "max": price_max
            },
            "currency": "MAD",
            "condition_factor": factor,
            "note": "Estimated via Direct Market Data"
        }
        
    
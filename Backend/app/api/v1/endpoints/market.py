from fastapi import APIRouter, HTTPException
import logging
from typing import Dict, Any, List
from app.tools.sql_inventory import get_csv_statistics, check_inventory, get_model_price_history, inventory_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market", tags=["market"])

@router.get("/brands")
async def get_market_brands() -> Dict[str, Any]:
    """
    Retourner la liste des marques disponibles.
    """
    try:
        brands = inventory_manager.get_unique_brands()
        return {"brands": brands}
    except Exception as e:
        logger.error(f"[market] Error getting brands: {e}")
        return {"brands": []}

@router.get("/statistics")
async def get_market_statistics() -> Dict[str, Any]:
    """
    Retourner les statistiques du marché depuis le CSV.
    """
    try:
        stats = await get_csv_statistics()
        if "error" in stats:
            raise Exception(stats["error"])

        return {
            "avg_price": stats.get("price_range", {}).get("avg", 0),
            "min_price": stats.get("price_range", {}).get("min", 0),
            "max_price": stats.get("price_range", {}).get("max", 0),
            "avg_mileage": stats.get("mileage_range", {}).get("avg", 0),
            "total_vehicles": stats.get("total_stock", 0),
            "trend": "stable",
            "demand_score": 50,
        }
    except Exception as e:
        logger.error(f"[market] Error getting statistics: {e}")
        return {
            "avg_price": 0,
            "min_price": 0,
            "max_price": 0,
            "avg_mileage": 0,
            "total_vehicles": 0,
            "trend": "stable",
            "demand_score": 0,
            "error": str(e)
        }

@router.get("/statistics/{model}")
async def get_market_statistics_by_model(model: str) -> Dict[str, Any]:
    """
    Retourner les statistiques du marché pour un modèle spécifique.
    """
    try:
        # Rechercher le modèle ou la marque dans l'inventaire
        inventory_data = await check_inventory({
            "query": model,
            "available": True
        })
        
        if inventory_data.get("stock_count", 0) > 0:
            avg_price = inventory_data.get("avg_price", 0)
            models = inventory_data.get("available_models", [])
            
            # Extraire min/max prices des modèles trouvés
            prices = [m.get("prix_estime", avg_price) for m in models if m.get("prix_estime")]
            
            return {
                "avg_price": avg_price,
                "min_price": min(prices) if prices else avg_price * 0.9,
                "max_price": max(prices) if prices else avg_price * 1.1,
                "avg_mileage": inventory_data.get("avg_mileage", 0),
                "total_vehicles": inventory_data.get("stock_count", 0),
                "trend": "stable",
                "demand_score": 50,
            }
        else:
            return {
                "avg_price": 0,
                "min_price": 0,
                "max_price": 0,
                "avg_mileage": 0,
                "total_vehicles": 0,
                "trend": "stable",
                "demand_score": 0,
                "no_data": True
            }
            
    except Exception as e:
        logger.error(f"[market] Error getting statistics for {model}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chart/{model}")
async def get_market_chart(model: str) -> List[Dict[str, Any]]:
    """
    Retourner les données de graphiques pour un modèle spécifique.
    """
    try:
        return await get_model_price_history(model)
    except Exception as e:
        logger.error(f"[market] Error getting chart for {model}: {e}")
        return []

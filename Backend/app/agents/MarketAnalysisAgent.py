# Halima: Market Analysis Agent

# Responsibility: Analyze stock availability and current SUV market trends.
# Tools: sql_inventory.py
# Tasks:
# 1. Implement search_inventory() to find matching vehicles for user trade-ins.
# 2. Add market_sentiment_analysis() to identify high-demand models.
# 3. Output a MarketContext object with stock availability levels.
# MarketAnalysisAgent.py
# Responsibility: Analyze stock availability and current SUV market trends
# Framework: Agno with Mistral-small-latest
# Author: Halima (OMEGA Team)
from app.agents.base import BaseOmegaAgent
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging
from agno.agent import Agent
import os

# Make sure you load your .env variables first (if using python-dotenv)
from dotenv import load_dotenv
load_dotenv()


# Import des fonctions CSV depuis votre sql_inventory.py
from ..tools.sql_inventory import check_inventory, get_vehicle_stock_levels, update_demand_metrics, update_vehicle_status, get_csv_statistics


class MarketAnalysisAgent(BaseOmegaAgent):
    """
    Market Insight & Inventory Agent.
    
    This agent specializes in analyzing automobile market trends and 
    showroom inventory. It identifies high-demand models, evaluates 
    stock levels, and provides strategic market context for the 
    negotiation process.
    
    Uses: cars_market.csv as the primary data source.
    """
    
    def __init__(self):
        """Initialize the Market Analysis Agent with Agno configuration."""
        
        self.agent = Agent(
            name="MarketAnalysisAgent",
            role="Analyste Marché et Inventaire",
            instructions= '''Tu es un expert en analyse de marché automobile avec 15 ans d'expérience.
                Ta mission est de fournir un contexte précis sur les stocks et tendances SUV pour optimiser la négociation.
                Tu comprends les cycles de demande, les variations saisonnières, et tu sais identifier les opportunités commerciales.''',
            tools=[self.search_inventory, self.market_sentiment_analysis, self.get_stock_levels],
        )
        
        # Configuration des seuils d'analyse
        self.stock_thresholds = {
            "critique": 5,
            "bas": 15,
            "moyen": 30,
            "élevé": 50
        }
        
        # Modèles SUV haute demande (adaptés au marché français)
        self.high_demand_models = [
            "3008", "2008", "5008",  # Peugeot
            "Captur", "Kadjar", "Austral",  # Renault
            "C5 Aircross", "C3 Aircross",  # Citroën
            "Duster",  # Dacia
            "Tiguan", "T-Roc", "T-Cross",  # Volkswagen
            "Qashqai", "Juke",  # Nissan
            "RAV4", "C-HR"  # Toyota
        ]
            
  
    async def search_inventory(
        self, 
        model: str, 
        brand: str = None, 
        max_price: float = None,
        category: str = "SUV"
    ) -> Dict[str, Any]:
        """
        Task 1: Rechercher les véhicules correspondants dans l'inventaire CSV.
        
        Args:
            model: Le modèle de véhicule recherché
            brand: La marque (correspond à 'mark' dans le CSV)
            max_price: Prix maximum estimé
            category: Catégorie de véhicule (défaut: "SUV")
            
        Returns:
            Dict contenant les véhicules disponibles et leur statut
        """
        
        search_params = {
            "model": model,
            "brand": brand,
            "category": category,
            "max_price": max_price,
            "available": True  # Seulement les véhicules avec quantity > 0
        }
        
        # Appel à la fonction CSV check_inventory
        inventory_data = await check_inventory(search_params)
        
        # Extraction des données
        stock_count = inventory_data.get("stock_count", 0)
        available_models = inventory_data.get("available_models", [])
        avg_price = inventory_data.get("avg_price", 0)
        
        # Enrichissement de l'analyse
        stock_level = self._evaluate_stock_level(stock_count)
        
        result = {
            "model": model,
            "brand": brand,
            "stock_count": stock_count,
            "stock_level": stock_level,
            "available_models": available_models,
            "total_vehicles_found": inventory_data.get("total_vehicles_found", 0),
            "avg_price": avg_price,
            "timestamp": datetime.now().isoformat(),
            "recommendation": self._generate_stock_recommendation(stock_level, model, stock_count)
        }
        
        return result
    
    async def get_stock_levels(self, category: str = "SUV") -> Dict[str, Any]:
        """
        Task 2: Obtenir les niveaux de stock globaux par catégorie.
        
        Args:
            category: Catégorie de véhicule (défaut: "SUV")
            
        Returns:
            Dict avec niveaux de stock par modèle
        """
        
        # Appel à la fonction CSV get_vehicle_stock_levels
        stock_data = await get_vehicle_stock_levels(category)
        
        total_vehicles = stock_data.get("total_vehicles", 0)
        models_count = stock_data.get("models_in_stock", 0)
        stock_by_model = stock_data.get("stock_by_model", [])
        
        # Enrichissement avec analyse
        result = {
            "category": category,
            "total_vehicles": total_vehicles,
            "models_in_stock": models_count,
            "stock_by_model": stock_by_model,
            "market_overview": self._generate_market_overview(stock_by_model),
            "top_models": stock_by_model[:5] if stock_by_model else [],
            "timestamp": datetime.now().isoformat()
        }
        
        return result
   
    async def market_sentiment_analysis(self, model: str = None) -> Dict[str, Any]:
        """
        Task 3: Analyser le sentiment et la demande du marché pour les SUV.
        
        Args:
            model: Modèle spécifique à analyser (optionnel)
            
        Returns:
            Dict contenant l'analyse de sentiment et les tendances
        """
        
        # Récupération des métriques de demande depuis le CSV
        demand_data = await update_demand_metrics(model)
        
        # Extraction des données
        demand_score = demand_data.get("demand_score", 0)
        supply_score = demand_data.get("supply_score", 0)
        trend_direction = demand_data.get("trend_direction", "stable")
        trending_models = demand_data.get("trending_models", [])
        
        # Analyse de tendance enrichie
        trend_analysis = {
            "overall_demand": self._calculate_demand_level(demand_score),
            "demand_score": demand_score,
            "supply_score": supply_score,
            "seasonal_factor": self._get_seasonal_factor(),
            "high_demand_models": trending_models,
            "market_sentiment": self._interpret_trend(trend_direction),
            "trend_direction": trend_direction,
            "price_pressure": self._evaluate_price_pressure(demand_score, supply_score),
            "timestamp": datetime.now().isoformat()
        }
        
        # Ajout de recommandations spécifiques pour un modèle
        if model:
            is_high_demand = any(
                model.lower() in trending.lower() 
                for trending in self.high_demand_models
            )
            
            trend_analysis["model_specific"] = {
                "name": model,
                "is_high_demand": is_high_demand,
                "is_trending": any(model.lower() in t.lower() for t in trending_models),
                "negotiation_leverage": self._calculate_negotiation_leverage(
                    model, demand_score, supply_score
                ),
                "recommendation": self._generate_market_recommendation(
                    model, demand_score, is_high_demand
                )
            }
        
        return trend_analysis
    
    async def analyze_market(
        self, 
        model: str, 
        brand: str = None, 
        user_budget: float = None
    ) -> Dict[str, Any]:
        """
        Fonction principale: Analyse complète du marché et contexte.
        
        Args:
            model: Modèle de véhicule
            brand: Marque du véhicule (correspond à 'mark' dans CSV)
            user_budget: Budget maximum du client
            
        Returns:
            MarketContext complet avec stocks, tendances et recommandations
        """
        
        # Exécution des tâches d'analyse en parallèle pour optimiser la vitesse
        import asyncio
        results = await asyncio.gather(
            self.search_inventory(model, brand, user_budget),
            self.market_sentiment_analysis(model),
            self.get_stock_levels("SUV")
        )
        
        inventory_result, sentiment_result, stock_levels = results
        
        # Construction du contexte marché
        market_context = {
            "analysis_date": datetime.now().isoformat(),
            "target_model": model,
            "target_brand": brand,
            "user_budget": user_budget,
            
            # Données d'inventaire
            "inventory": {
                "stock_available": inventory_result["stock_count"],
                "stock_level": inventory_result["stock_level"],
                "available_units": inventory_result["available_models"],
                "total_vehicles_found": inventory_result["total_vehicles_found"],
                "avg_market_price": inventory_result["avg_price"]
            },
            
            # Analyse de marché
            "market_trends": {
                "demand_level": sentiment_result["overall_demand"],
                "demand_score": sentiment_result["demand_score"],
                "supply_score": sentiment_result["supply_score"],
                "seasonal_impact": sentiment_result["seasonal_factor"],
                "market_sentiment": sentiment_result["market_sentiment"],
                "price_pressure": sentiment_result["price_pressure"],
                "trending_models": sentiment_result["high_demand_models"],
                "trend_direction": sentiment_result["trend_direction"]
            },
            
            # Vue d'ensemble du marché SUV
            "market_overview": {
                "total_suv_stock": stock_levels["total_vehicles"],
                "models_available": stock_levels["models_in_stock"],
                "top_models": stock_levels["top_models"]
            },
            
            # Recommandations stratégiques
            "strategic_insights": {
                "inventory_recommendation": inventory_result["recommendation"],
                "market_recommendation": sentiment_result.get("model_specific", {}).get(
                    "recommendation", "Analyse en cours"
                ),
                "negotiation_position": self._determine_negotiation_position(
                    inventory_result, sentiment_result
                ),
                "urgency_level": self._calculate_urgency(
                    inventory_result, sentiment_result
                ),
                "price_flexibility": self._calculate_price_flexibility(
                    inventory_result["stock_level"],
                    sentiment_result["demand_score"]
                )
            },
            
            # Métriques pour autres agents (Orchestrator, Negotiation, etc.)
            "agent_context": {
                "can_offer_discount": inventory_result["stock_level"] in ["élevé", "moyen"],
                "should_push_alternative": inventory_result["stock_count"] < 3,
                "market_leverage": sentiment_result.get("model_specific", {}).get(
                    "negotiation_leverage", 0.5
                ),
                "stock_urgency": inventory_result["stock_count"] <= self.stock_thresholds["critique"],
                "demand_urgency": sentiment_result["demand_score"] >= 100,
                "budget_compatible": self._check_budget_compatibility(
                    user_budget, inventory_result["avg_price"]
                )
            }
        }
        
        return market_context
    
    async def get_csv_stats(self) -> Dict[str, Any]:
        """
        Obtenir les statistiques générales du CSV.
        Utile pour le monitoring et le debugging.
        
        Returns:
            Dict avec statistiques complètes du CSV
        """
        stats = await get_csv_statistics()
        return stats
    
    async def update_stock(
        self, 
        brand: str, 
        model: str, 
        quantity_change: int = -1
    ) -> bool:
        """
        Mettre à jour le stock d'un véhicule (après vente, réservation, etc.)
        
        Args:
            brand: Marque (correspond à 'mark')
            model: Modèle
            quantity_change: Changement de quantité (ex: -1 pour une vente)
            
        Returns:
            bool: True si succès
        """
        
        success = await update_vehicle_status(
            brand=brand,
            model=model,
            new_status="sold" if quantity_change < 0 else "available",
            quantity_change=quantity_change
        )
        

        
        return success
    
    # ============================================
    # Méthodes Utilitaires Privées
    # ============================================
    
    def _evaluate_stock_level(self, stock_count: int) -> str:
        """Évalue le niveau de stock selon les seuils définis."""
        if stock_count <= self.stock_thresholds["critique"]:
            return "critique"
        elif stock_count <= self.stock_thresholds["bas"]:
            return "bas"
        elif stock_count <= self.stock_thresholds["moyen"]:
            return "moyen"
        else:
            return "élevé"
    
    def _generate_stock_recommendation(
        self, 
        stock_level: str, 
        model: str, 
        stock_count: int
    ) -> str:
        recommendations = {
            "critique": f" Stock critique pour {model} ({stock_count} unités). "
                       f"Recommandation: proposer des modèles alternatifs ou accélérer la négociation. "
                       f"Valoriser la rareté.",
            
            "bas": f" Stock bas pour {model} ({stock_count} unités). "
                   f"Limiter les remises, valoriser la disponibilité immédiate. "
                   f"Position de négociation favorable.",
            
            "moyen": f" Stock satisfaisant pour {model} ({stock_count} unités). "
                    f"Marge de négociation modérée possible. Équilibre entre volume et rentabilité.",
            
            "élevé": f"Stock élevé pour {model} ({stock_count} unités). "
                    f"Possibilité d'offrir des conditions avantageuses pour écouler le stock. "
                    f"Flexibilité sur le prix recommandée."
        }
        return recommendations.get(stock_level, "Analyse en cours.")
    
    def _calculate_demand_level(self, demand_score: int) -> str:
        """Calculer le niveau de demande textuel depuis le score."""
        if demand_score >= 120:
            return "très élevée"
        elif demand_score >= 100:
            return "élevée"
        elif demand_score >= 70:
            return "modérée"
        elif demand_score >= 40:
            return "faible"
        else:
            return "très faible"
    
    def _interpret_trend(self, trend_direction: str) -> str:
        """Interpréter la direction de tendance en sentiment."""
        if trend_direction == "up":
            return "positif"
        elif trend_direction == "down":
            return "négatif"
        else:
            return "stable"
    
    def _get_seasonal_factor(self) -> str:
        """Déterminer l'impact saisonnier sur la demande SUV."""
        month = datetime.now().month
        
        # Forte demande: septembre (rentrée), mars (printemps)
        if month in [3, 9]:
            return "haute saison"
        # Demande modérée
        elif month in [1, 2, 5, 6, 10, 11]:
            return "saison normale"
        # Basse demande: été et décembre
        else:
            return "basse saison"
    
    def _evaluate_price_pressure(self, demand_score: int, supply_score: int) -> str:
        """Évaluer la pression sur les prix basée sur offre/demande."""
        if supply_score == 0:
            return "indéterminé (pas de stock)"
        
        ratio = demand_score / supply_score
        
        if ratio > 1.5:
            return "forte pression à la hausse"
        elif ratio > 1.0:
            return "légère pression à la hausse"
        elif ratio > 0.7:
            return "stable"
        else:
            return "pression à la baisse"
    
    def _calculate_negotiation_leverage(
        self, 
        model: str, 
        demand_score: int, 
        supply_score: int
    ) -> float:
        """
        Calculer le levier de négociation (0-1 scale).
        Plus le score est élevé, plus le vendeur a de levier.
        """
        # Vérifier si c'est un modèle haute demande
        is_high_demand = any(
            model.lower() in high_demand.lower() 
            for high_demand in self.high_demand_models
        )
        
        # Formule de leverage
        leverage = 0.5  # Base neutre
        
        # Bonus si modèle haute demande
        if is_high_demand:
            leverage += 0.2
        
        # Ajustement selon score de demande
        if demand_score >= 100:
            leverage += 0.2
        elif demand_score >= 70:
            leverage += 0.1
        elif demand_score < 40:
            leverage -= 0.2
        
        # Ajustement selon stock (supply)
        if supply_score <= 10:
            leverage += 0.1  # Stock faible = plus de levier
        elif supply_score >= 30:
            leverage -= 0.1  # Stock élevé = moins de levier
        
        # Garder entre 0 et 1
        return max(0.0, min(1.0, leverage))
    
    def _generate_market_recommendation(
        self, 
        model: str, 
        demand_score: int, 
        is_high_demand: bool
    ) -> str:
        """Générer une recommandation stratégique de marché."""
        if demand_score >= 100:
            return (
                f"🔥 {model} en très forte demande (score: {demand_score}). "
                f"Position de force: limiter les concessions, valoriser l'exclusivité et la disponibilité. "
                f"Possibilité de vente rapide au prix fort."
            )
        elif demand_score >= 70:
            return (
                f"📈 {model} en bonne demande (score: {demand_score}). "
                f"Stratégie équilibrée: maintenir des prix compétitifs tout en préservant la marge. "
                f"Flexibilité modérée possible."
            )
        elif demand_score >= 40:
            return (
                f"➡️ Demande modérée pour {model} (score: {demand_score}). "
                f"Stratégie: être flexible sur le prix, mettre en avant les avantages et options. "
                f"Négociation constructive recommandée."
            )
        else:
            return (
                f"⚠️ Demande faible pour {model} (score: {demand_score}). "
                f"Stratégie active: proposer des offres attractives, packages, ou alternatives. "
                f"Valoriser les spécificités du véhicule."
            )
    
    def _determine_negotiation_position(
        self, 
        inventory_result: Dict, 
        sentiment_result: Dict
    ) -> str:
        """Déterminer la position de négociation globale."""
        stock_level = inventory_result["stock_level"]
        demand_score = sentiment_result["demand_score"]
        
        if stock_level in ["critique", "bas"] and demand_score >= 100:
            return "position très forte (stock rare + forte demande)"
        elif stock_level in ["critique", "bas"] and demand_score >= 70:
            return "position forte (stock limité + demande soutenue)"
        elif stock_level == "élevé" and demand_score < 40:
            return "position faible (surstock + faible demande)"
        elif stock_level == "élevé" and demand_score < 70:
            return "position modérée (stock élevé + demande limitée)"
        else:
            return "position équilibrée (offre et demande alignées)"
    
    def _calculate_urgency(
        self, 
        inventory_result: Dict, 
        sentiment_result: Dict
    ) -> str:
        """Calculer le niveau d'urgence de la transaction."""
        stock_count = inventory_result["stock_count"]
        demand_score = sentiment_result["demand_score"]
        
        if stock_count <= 2 and demand_score >= 100:
            return "très urgente (risque de rupture immédiate)"
        elif stock_count <= 5 and demand_score >= 70:
            return "urgente (stock limité + demande forte)"
        elif stock_count > 40 and demand_score < 40:
            return "urgente (écoulement de stock nécessaire)"
        elif stock_count <= 10:
            return "modérée (stock limité)"
        else:
            return "normale (situation stable)"
    
    def _calculate_price_flexibility(self, stock_level: str, demand_score: int) -> str:
        """Calculer la flexibilité de prix recommandée."""
        if stock_level == "élevé" and demand_score < 40:
            return "élevée (jusqu'à 10-15% de remise possible)"
        elif stock_level in ["élevé", "moyen"]:
            return "modérée (5-8% de remise envisageable)"
        elif stock_level == "bas" or demand_score >= 100:
            return "faible (2-3% maximum)"
        elif stock_level == "critique":
            return "très faible (prix ferme recommandé)"
        else:
            return "modérée (négociation cas par cas)"
    
    def _generate_market_overview(self, stock_by_model: List[Dict]) -> Dict[str, Any]:
        """Générer une vue d'ensemble du marché."""
        if not stock_by_model:
            return {
                "status": "Aucune donnée disponible",
                "top_stock": None,
                "low_stock": None
            }
        
        # Trier par stock
        sorted_by_stock = sorted(
            stock_by_model, 
            key=lambda x: x.get('stock_count', 0), 
            reverse=True
        )
        
        return {
            "top_stock_models": sorted_by_stock[:3],
            "low_stock_models": sorted_by_stock[-3:] if len(sorted_by_stock) >= 3 else sorted_by_stock,
            "avg_stock_per_model": sum(m.get('stock_count', 0) for m in stock_by_model) / len(stock_by_model),
            "total_models": len(stock_by_model)
        }
    
    def _check_budget_compatibility(
        self, 
        user_budget: Optional[float], 
        avg_price: float
    ) -> str:
        """Vérifier la compatibilité du budget avec le prix moyen."""
        if not user_budget or avg_price == 0:
            return "indéterminé"
        
        ratio = user_budget / avg_price
        
        if ratio >= 1.2:
            return "largement compatible"
        elif ratio >= 1.0:
            return "compatible"
        elif ratio >= 0.9:
            return "ajusté (négociation nécessaire)"
        elif ratio >= 0.8:
            return "serré (forte négociation requise)"
        else:
            return "insuffisant (alternatives à proposer)"


# ============================================
# Classe de Modèle de Données
# ============================================

class MarketContext:
    """
    Modèle de données structuré pour le contexte marché.
    Utilisé pour la communication avec les autres agents.
    """
    def __init__(self, data: Dict[str, Any]):
        self.analysis_date = data.get("analysis_date")
        self.target_model = data.get("target_model")
        self.target_brand = data.get("target_brand")
        self.user_budget = data.get("user_budget")
        self.inventory = data.get("inventory", {})
        self.market_trends = data.get("market_trends", {})
        self.market_overview = data.get("market_overview", {})
        self.strategic_insights = data.get("strategic_insights", {})
        self.agent_context = data.get("agent_context", {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "analysis_date": self.analysis_date,
            "target_model": self.target_model,
            "target_brand": self.target_brand,
            "user_budget": self.user_budget,
            "inventory": self.inventory,
            "market_trends": self.market_trends,
            "market_overview": self.market_overview,
            "strategic_insights": self.strategic_insights,
            "agent_context": self.agent_context
        }
    
    def __str__(self) -> str:
        """String representation for logging."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    def get_summary(self) -> str:
        """Obtenir un résumé textuel pour les autres agents."""
        return f"""
🎯 Analyse Marché - {self.target_brand} {self.target_model}

📦 Inventaire:
  - Stock disponible: {self.inventory.get('stock_available', 0)} unités
  - Niveau: {self.inventory.get('stock_level', 'N/A')}
  - Prix moyen: {self.inventory.get('avg_market_price', 0):.2f}€

📈 Marché:
  - Demande: {self.market_trends.get('demand_level', 'N/A')} (score: {self.market_trends.get('demand_score', 0)})
  - Tendance: {self.market_trends.get('trend_direction', 'stable')}
  - Sentiment: {self.market_trends.get('market_sentiment', 'N/A')}

💡 Recommandations:
  - Position négociation: {self.strategic_insights.get('negotiation_position', 'N/A')}
  - Urgence: {self.strategic_insights.get('urgency_level', 'N/A')}
  - Flexibilité prix: {self.strategic_insights.get('price_flexibility', 'N/A')}
        """.strip()


# ============================================
# Fonction de test/démo
# ============================================

async def demo_market_analysis():
    """Fonction de démonstration de l'agent."""
    
    # Initialiser l'agent
    agent = MarketAnalysisAgent()
    
    # Exemple d'analyse complète
    result = await agent.analyze_market(
        model="3008",
        brand="Peugeot",
        user_budget=30000.0
    )
    
    # Afficher les résultats
    context = MarketContext(result)
    print("\n" + context.get_summary())
    print("\n" + "="*60)
    
    # Statistiques CSV
    stats = await agent.get_csv_stats()
    print(f"\n📊 Statistiques CSV:")
    print(f"  - Total véhicules: {stats.get('total_rows', 0)}")
    print(f"  - Stock total: {stats.get('total_stock', 0)} unités")
    print(f"  - Marques uniques: {stats.get('unique_brands', 0)}")
    print(f"  - Modèles uniques: {stats.get('unique_models', 0)}")
    
    return result


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_market_analysis())
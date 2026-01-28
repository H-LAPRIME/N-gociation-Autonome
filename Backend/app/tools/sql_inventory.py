# Gestionnaire de stock et d'inventaire SQL (Responsabilité: Halima).
# Ce module exécute des requêtes de base de données (PostgreSQL/MySQL) pour :
# 1. Vérifier la disponibilité des véhicules SUV critiques.
# 2. Consulter les prix de vente actuels dans l'inventaire local.
# 3. Mettre à jour l'état du stock après une offre validée.

import asyncio
import pandas as pd
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from pathlib import Path
import os


# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# Configuration Fichiers
# ============================================

# Chemin vers le fichier CSV
CSV_FILE_PATH = os.path.join(os.path.dirname(__file__), "data/cars_market.csv")

# ============================================
# Classe de Gestion CSV
# ============================================

class CSVInventoryManager:
    """Gestionnaire d'inventaire basé sur cars_market.csv."""
    
    def __init__(self, csv_path: str = CSV_FILE_PATH):
        """
        Initialize the CSV inventory manager.
        
        Args:
            csv_path: Chemin vers le fichier cars_market.csv
        """
        self.csv_path = csv_path
        self.df = None
        self._load_data()
    
    def _load_data(self):
        """Charger les données du CSV."""
        try:
            if os.path.exists(self.csv_path):
                self.df = pd.read_csv(self.csv_path)
                
                # Normaliser les noms de colonnes
                self.df.columns = self.df.columns.str.lower().str.strip()

                
                
                # Ajouter des colonnes calculées utiles
                self._enrich_data()
                
            else:
                logger.error(f"❌ Fichier CSV introuvable: {self.csv_path}")
                raise FileNotFoundError(f"Le fichier {self.csv_path} n'existe pas")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement du CSV: {e}")
            raise
    
    def _enrich_data(self):
        """Enrichir les données avec des colonnes calculées."""
        # Ajouter colonne 'disponible' basée sur quantity
        self.df['disponible'] = self.df['quantity'] > 0
        
        # Calculer un prix estimé basé sur l'année et la marque
        # (à ajuster selon vos besoins)
        self.df['prix_estime'] = self._estimate_price(self.df)
        
        # Catégoriser les véhicules
        self.df['categorie'] = self.df['modele'].apply(self._categorize_vehicle)
        
    
    def _estimate_price(self, df: pd.DataFrame) -> pd.Series:
        """
        Estimer le prix basé sur l'année et la marque.
        Prix de base + ajustement selon marque + dépréciation par année.
        """
        current_year = datetime.now().year
        
        # Prix de base par marque (en euros)
        brand_base_prices = {
            'mercedes-benz': 35000, 'bmw': 33000, 'audi': 32000,
            'porsche': 70000, 'bentley': 150000, 'jaguar': 40000,
            'land rover': 45000, 'tesla': 50000,
            'volkswagen': 25000, 'renault': 22000, 'peugeot': 20000,
            'citroen': 19000, 'dacia': 15000, 'seat': 18000,
            'ford': 22000, 'opel': 18000, 'fiat': 16000,
            'toyota': 25000, 'honda': 24000, 'nissan': 23000,
            'hyundai': 20000, 'kia': 19000, 'suzuki': 17000,
            'mini': 28000, 'volvo': 35000
        }
        
        prices = []
        for _, row in df.iterrows():
            brand = str(row['mark']).lower()
            year = row['year']
            
            # Prix de base selon la marque
            base_price = brand_base_prices.get(brand, 20000)
            
            # Gérer les années spéciales
            if isinstance(year, str) or year < 1980:
                year = 1980
            
            # Dépréciation: -8% par an depuis année en cours
            years_old = max(0, current_year - year)
            depreciation = 1 - (years_old * 0.08)
            depreciation = max(0.2, min(1.0, depreciation))  # Entre 20% et 100%
            
            estimated_price = base_price * depreciation
            prices.append(round(estimated_price, 2))
        
        return pd.Series(prices)
    
    def _categorize_vehicle(self, model: str) -> str:
        """Catégoriser le véhicule selon son modèle."""
        model_lower = str(model).lower()
        
        # SUV keywords
        suv_keywords = ['suv', 'qashqai', 'tiguan', 'tucson', 'sportage', 'duster', 
                        'captur', 'kadjar', '3008', '2008', '5008', 'rav', 'cr-v', 
                        'hr-v', 'x-trail', 'range', 'defender', 'cayenne', 'macan',
                        'q3', 'q5', 'q7', 'q8', 'x1', 'x3', 'x5', 'x6', 'glc', 'gle',
                        'gla', 'outlander', 'santa', 'creta', 'ix', 'ecosport', 'kuga',
                        'evoque', 'c-hr', 'yaris cross', 'prado', 'compass', 'renegade',
                        'cherokee', 'grand cherokee', 'touareg', 'kodiaq', 'karoq']
        
        # Berline/Sedan keywords
        sedan_keywords = ['sedan', 'serie', 'classe', 'passat', 'jetta', 'accord',
                         'camry', 'mondeo', 'insignia', 'superb', 'octavia']
        
        # Utilitaire keywords
        utility_keywords = ['caddy', 'partner', 'berlingo', 'kangoo', 'doblo',
                           'combo', 'transit', 'ducato', 'vito', 'hilux', 'amarok',
                           'ranger', 'l200', 'dokker', 'bipper', 'rifter', 'tepee']
        
        # Citadine keywords
        city_keywords = ['polo', 'clio', '208', '207', '206', 'fiesta', 'corsa',
                        'micra', 'yaris', 'aygo', 'picanto', 'i10', 'up', 'twingo',
                        'sandero', 'logan', 'punto', 'panda', '500', 'spark', 'qq']
        
        if any(keyword in model_lower for keyword in suv_keywords):
            return 'SUV'
        elif any(keyword in model_lower for keyword in utility_keywords):
            return 'Utilitaire'
        elif any(keyword in model_lower for keyword in sedan_keywords):
            return 'Berline'
        elif any(keyword in model_lower for keyword in city_keywords):
            return 'Citadine'
        else:
            return 'Autre'
    
    def reload_data(self):
        """Recharger les données du CSV."""
        self._load_data()
    
    def get_dataframe(self) -> pd.DataFrame:
        """Retourner le DataFrame complet."""
        return self.df.copy()
    
    def save_changes(self):
        """Sauvegarder les modifications dans le CSV."""
        try:
            # Sauvegarder seulement les colonnes originales
            original_cols = ['mark', 'modele', 'year', 'quantity']
            self.df[original_cols].to_csv(self.csv_path, index=False)
            return True
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde: {e}")
            return False


# Instance globale du gestionnaire
inventory_manager = CSVInventoryManager()


# ============================================
# Fonctions Principales (API)
# ============================================

async def check_inventory(search_params: dict) -> Dict[str, Any]:
    """
    Vérifier la disponibilité des véhicules dans l'inventaire CSV.
    
    Args:
        search_params: Dict contenant:
            - model: str (nom du modèle)
            - brand: str (marque - correspond à 'mark')
            - category: str (ex: "SUV")
            - max_price: float (prix maximum estimé)
            - available: bool (seulement disponibles - quantity > 0)
    
    Returns:
        Dict avec stock_count, available_models, avg_price
    """
    try:
        # Extraction des paramètres
        model = search_params.get("model", "")
        brand = search_params.get("brand")
        category = search_params.get("category")
        max_price = search_params.get("max_price")
        available_only = search_params.get("available", True)
                
        # Recharger les données
        inventory_manager.reload_data()
        df = inventory_manager.get_dataframe()
        
        filtered_df = df.copy()

        # Filtre catégorie
        if category and 'categorie' in filtered_df.columns:
            filtered_df = filtered_df[
                filtered_df['categorie'].str.lower() == category.strip().lower()
            ]
        
        # Filtre disponibilité (quantity > 0)
        if available_only:
            filtered_df = filtered_df[filtered_df['quantity'] > 0]
        
        # Filtre marque (brand)
        if brand and isinstance(brand, str) and brand.strip():
            filtered_df = filtered_df[
                filtered_df['mark'].str.lower().str.contains(brand.strip().lower(), na=False)
            ]
        
        # Filtre modèle (model)
        if model and isinstance(model, str) and model.strip():
            filtered_df = filtered_df[
                filtered_df['modele'].str.lower().str.contains(model.strip().lower(), na=False)
            ]
        
        # Filtre prix maximum
        if max_price and 'prix_estime' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['prix_estime'] <= max_price]
                
        # Calculer les résultats
        if len(filtered_df) > 0:
            stock_count = int(filtered_df['quantity'].sum())
            avg_price = float(filtered_df['prix_estime'].mean())
            available_models = filtered_df.to_dict('records')

            # Nettoyer les NaN
            for model_dict in available_models:
                for key, value in model_dict.items():
                    if pd.isna(value):
                        model_dict[key] = None
        else:
            stock_count = 0
            avg_price = 0
            available_models = []
        
        result = {
            "stock_count": stock_count,
            "available_models": available_models,
            "avg_price": round(avg_price, 2),
            "query_timestamp": datetime.now().isoformat(),
            "search_params": search_params,
            "total_vehicles_found": len(filtered_df)
        }
        
        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "stock_count": 0,
            "available_models": [],
            "avg_price": 0,
            "error": str(e)
        }


async def get_vehicle_stock_levels(category: str = "SUV") -> Dict[str, Any]:
    """
    Obtenir les niveaux de stock globaux par catégorie.
    
    Args:
        category: Catégorie de véhicule (défaut: "SUV")
    
    Returns:
        Dict avec niveaux de stock par modèle
    """
    try:
        
        # Recharger les données
        inventory_manager.reload_data()
        df = inventory_manager.get_dataframe()
        
        # Filtrer par catégorie si spécifié
        if category and category.lower() != 'all':
            df = df[df['categorie'].str.lower() == category.lower()]
        
        # Grouper par marque et modèle
        grouped = df.groupby(['mark', 'modele']).agg({
            'quantity': 'sum',
            'prix_estime': ['mean', 'min', 'max'],
            'year': ['min', 'max']
        }).reset_index()
        
        # Aplatir les colonnes multi-index
        grouped.columns = ['mark', 'modele', 'stock_count', 'avg_price', 
                          'min_price', 'max_price', 'min_year', 'max_year']
        
        # Ajouter colonne available_count (véhicules avec stock > 0)
        grouped['available_count'] = grouped['stock_count'].apply(lambda x: 1 if x > 0 else 0)
        
        # Trier par stock décroissant
        grouped = grouped.sort_values('stock_count', ascending=False)
        
        # Convertir en liste de dictionnaires
        stock_data = grouped.to_dict('records')
        
        # Nettoyer les NaN et formater
        for item in stock_data:
            for key, value in item.items():
                if pd.isna(value):
                    item[key] = 0
                elif key in ['stock_count', 'available_count']:
                    item[key] = int(value)
                elif key in ['min_year', 'max_year']:
                    try:
                        # Essayer de convertir normalement
                        item[key] = int(value)
                    except (ValueError, TypeError):
                        # Si impossible, extraire le chiffre au début (ex: "1980 ou plus ancien" -> 1980)
                        import re
                        match = re.search(r'\d+', str(value))
                        item[key] = int(match.group(0)) if match else 0
                elif key in ['avg_price', 'min_price', 'max_price']:
                    item[key] = round(float(value), 2)
        
        total_vehicles = int(grouped['stock_count'].sum())
        
        result = {
            "category": category,
            "total_vehicles": total_vehicles,
            "models_in_stock": len(stock_data),
            "stock_by_model": stock_data,
            "timestamp": datetime.now().isoformat()
        }
        
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "category": category,
            "total_vehicles": 0,
            "models_in_stock": 0,
            "stock_by_model": [],
            "error": str(e)
        }


async def update_demand_metrics(model: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculer les métriques de demande basées sur le stock disponible.
    
    Logique: Stock faible = forte demande, stock élevé = faible demande
    
    Args:
        model: Modèle spécifique (optionnel)
    
    Returns:
        Dict avec métriques de demande et tendances
    """
    try:
        
        # Recharger les données
        inventory_manager.reload_data()
        df = inventory_manager.get_dataframe()
        
        # Filtrer par modèle si spécifié
        if model:
            model_df = df[df['modele'].str.lower().str.contains(model.lower(), na=False)]
        else:
            model_df = df
        
        # Calculer les métriques
        if len(model_df) > 0:
            total_stock = int(model_df['quantity'].sum())
            avg_stock_per_model = float(model_df['quantity'].mean())
            
            # Score de demande inversé: stock faible = forte demande
            if avg_stock_per_model <= 5:
                demand_score = 120  # Très forte demande
            elif avg_stock_per_model <= 10:
                demand_score = 100  # Forte demande
            elif avg_stock_per_model <= 15:
                demand_score = 70   # Demande modérée
            else:
                demand_score = 40   # Faible demande
            
            supply_score = int(avg_stock_per_model)
            
            # Identifier les modèles tendance (stock le plus faible = plus demandés)
            # Exclure les modèles avec stock = 0
            available_df = model_df[model_df['quantity'] > 0]
            if len(available_df) >= 5:
                trending_df = available_df.nsmallest(5, 'quantity')
                trending = [f"{row['mark']} {row['modele']}" 
                           for _, row in trending_df.iterrows()]
            else:
                trending = [f"{row['mark']} {row['modele']}" 
                           for _, row in available_df.head(5).iterrows()]
        else:
            total_stock = 0
            demand_score = 0
            supply_score = 0
            trending = []
        
        # Simuler des métriques d'engagement (basées sur le stock)
        page_views = demand_score * 10
        inquiries = int(demand_score * 0.5)
        conversions = int(inquiries * 0.3)
        
        # Calculer la tendance
        trend_direction = _calculate_trend_direction({
            "demand_score": demand_score,
            "supply_score": supply_score
        })
        
        result = {
            "model": model,
            "page_views": page_views,
            "inquiries": inquiries,
            "conversions": conversions,
            "demand_score": demand_score,
            "supply_score": supply_score,
            "trend_direction": trend_direction,
            "trending_models": trending,
            "total_stock": total_stock,
            "period": "données actuelles",
            "timestamp": datetime.now().isoformat()
        }
        
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "model": model,
            "page_views": 0,
            "inquiries": 0,
            "conversions": 0,
            "demand_score": 0,
            "supply_score": 0,
            "trend_direction": "stable",
            "trending_models": [],
            "error": str(e)
        }


async def update_vehicle_status(brand: str = None, model: str = None, 
                                new_status: str = "reserved", quantity_change: int = -1) -> bool:
    """
    Mettre à jour le statut/quantité d'un véhicule dans le CSV.
    
    Args:
        brand: Marque (correspond à 'mark' dans le CSV)
        model: Modèle
        new_status: Nouveau statut ("reserved", "sold", "available")
        quantity_change: Changement de quantité (ex: -1 pour vente)
    
    Returns:
        bool: True si succès, False sinon
    """
    try:
        
        # Recharger les données
        inventory_manager.reload_data()
        df = inventory_manager.get_dataframe()
        
        # Trouver le véhicule
        if brand and model:
            mask = (df['mark'].str.lower().str.contains(brand.lower(), na=False)) & \
                   (df['modele'].str.lower().str.contains(model.lower(), na=False))
        else:
            return False
        
        if mask.sum() == 0:
            return False
        
        # Mettre à jour la quantité
        if quantity_change != 0:
            df.loc[mask, 'quantity'] = df.loc[mask, 'quantity'] + quantity_change
            # S'assurer que la quantité ne devient pas négative
            df.loc[mask, 'quantity'] = df.loc[mask, 'quantity'].clip(lower=0)
        
        # Mettre à jour disponibilité
        df.loc[mask, 'disponible'] = df.loc[mask, 'quantity'] > 0
        
        # Sauvegarder dans le CSV
        inventory_manager.df = df
        success = inventory_manager.save_changes()

        
        return success
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False


# ============================================
# Fonctions Utilitaires
# ============================================

def _calculate_trend_direction(demand_data: Dict[str, Any]) -> str:
    """Calculer la direction de la tendance."""
    demand_score = demand_data.get("demand_score", 0)
    supply_score = demand_data.get("supply_score", 0)
    
    ratio = demand_score / max(supply_score, 1)
    
    if ratio > 1.5:
        return "up"
    elif ratio > 0.8:
        return "stable"
    else:
        return "down"


async def get_csv_statistics() -> Dict[str, Any]:
    """
    Obtenir des statistiques générales sur le CSV.
    """
    try:
        inventory_manager.reload_data()
        df = inventory_manager.get_dataframe()
        
        stats = {
            "total_rows": len(df),
            "columns": list(df.columns),
            "total_stock": int(df['quantity'].sum()),
            "available_vehicles": int((df['quantity'] > 0).sum()),
            "unique_brands": int(df['mark'].nunique()),
            "unique_models": int(df['modele'].nunique()),
            "year_range": {
                "min": int(df[df['year'].apply(lambda x: isinstance(x, int))]['year'].min()),
                "max": int(df[df['year'].apply(lambda x: isinstance(x, int))]['year'].max())
            },
            "price_range": {
                "min": float(df['prix_estime'].min()),
                "max": float(df['prix_estime'].max()),
                "avg": float(df['prix_estime'].mean())
            },
            "categories": df['categorie'].value_counts().to_dict(),
            "top_brands": df.groupby('mark')['quantity'].sum().nlargest(10).to_dict(),
            "timestamp": datetime.now().isoformat()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du calcul des statistiques: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


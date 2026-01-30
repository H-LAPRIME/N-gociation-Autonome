"""
Car Market Scraper Tool
-----------------------
Scrapes Moteur.ma to fetch real-time market prices for used vehicles in Morocco.
Includes caching and heuristic fallbacks for speed and reliability.
"""
import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import re
import logging
import time
import hashlib
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory cache with TTL
_scraper_cache = {}
CACHE_TTL_SECONDS = 86400  # 24 hours

def _get_cache_key(model: str, year: int, mileage: int) -> str:
    """Generate cache key from params"""
    data = f"{model.lower()}_{year}_{mileage//10000}"  # Group by 10k km increments
    return hashlib.md5(data.encode()).hexdigest()

async def get_vehicle_estimation(model: str, year: int, mileage: int) -> Dict[str, Any]:
    """
    Récupère une estimation de la valeur marchande d'un véhicule d'occasion au Maroc via Moteur.ma.
    OPTIMIZED with aggressive caching and reduced timeout.
    """
    # Check cache first
    cache_key = _get_cache_key(model, year, mileage)
    if cache_key in _scraper_cache:
        cached_time, cached_result = _scraper_cache[cache_key]
        if time.time() - cached_time < CACHE_TTL_SECONDS:
            logger.info(f"⚡ Cache HIT for {model} {year} (~{mileage//1000}k km)")
            return cached_result
    
    # 1. Construction de l'URL de recherche
    search_url = f"https://www.moteur.ma/fr/voiture/recherche/?modele={model.lower().replace(' ', '+')}&annee_min={year}&annee_max={year}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    prices = []
    
    try:
        # OPTIMIZATION: Reduced timeout from 10s to 3s
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(search_url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Les prix sont souvent dans des divs avec la classe 'price' ou '.prix'
                # ou dans les liens des annonces
                price_elements = soup.select(".price, .prix, .price-ads, .item-price")
                
                for el in price_elements:
                    price_text = el.get_text(strip=True)
                    # Nettoyage du texte (ex: "180 000 DH" -> 180000)
                    price_digits = re.sub(r'[^\d]', '', price_text)
                    if price_digits:
                        price_val = int(price_digits)
                        # Filtrer les prix aberrants (ex: frais de dossier ou erreurs)
                        if price_val > 10000: 
                            prices.append(price_val)
                
                # Si non trouvé, on cherche dans les liens d'annonces (parfois le prix y est)
                if not prices:
                    for link in soup.find_all('a', href=True):
                        # Souvent le prix est un enfant direct du lien d'annonce
                        text = link.get_text(strip=True)
                        if "DH" in text.upper():
                            digits = re.sub(r'[^\d]', '', text)
                            if digits and int(digits) > 10000:
                                prices.append(int(digits))

    except Exception as e:
        logger.warning(f"⚠️ Scraping timeout/error for {model}: {e}")

    # 2. Logique de repli (Fallback) si aucun prix trouvé
    if not prices:
        logger.info(f"💨 Using fast heuristic for {model} {year}")
        base_price = 220000  # Base SUV moyenne
        age_factor = (2026 - year) * 0.06
        mileage_factor = (mileage / 10000) * 0.012
        estimated = base_price * (1 - age_factor - mileage_factor)
        estimated = max(estimated, 30000)
        
        result = {
            "estimated_price": round(estimated, -2),
            "currency": "MAD",
            "source": "Heuristic Fallback"
        }
        
        # Cache fallback too
        _scraper_cache[cache_key] = (time.time(), result)
        return result

    # 3. Calcul de la moyenne
    avg_price = sum(prices) / len(prices)
    
    # Ajustement léger basé sur le kilométrage (le scraping donne une moyenne brute)
    # On considère une base de 15000km/an
    expected_mileage = (2026 - year) * 15000
    mileage_diff_ratio = (mileage - expected_mileage) / 100000
    avg_price = avg_price * (1 - mileage_diff_ratio * 0.1)

    result = {
        "estimated_price": round(avg_price, -2),
        "currency": "MAD",
        "sample_size": len(prices),
        "source": "Moteur.ma Scraper"
    }
    
    # Cache the result
    _scraper_cache[cache_key] = (time.time(), result)
    logger.info(f"✅ Cached estimation for {model} {year}")
    
    return result


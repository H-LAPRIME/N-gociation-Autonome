# Configuration centrale de l'application (Responsabilité: Moustapha).
# Gère les variables d'environnement (.env), les secrets API, et les réglages globaux.
# Utilise Pydantic Settings pour garantir que toutes les variables requises sont présentes au démarrage.

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Exemple: PROJECT_NAME: str = "OMEGA Backend"
    # Exemple: DATABASE_URL: str
    
    class Config:
        env_file = ".env"

settings = Settings()

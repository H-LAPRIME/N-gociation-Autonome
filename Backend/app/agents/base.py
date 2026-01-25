# Classe de base et Configuration des Agents (Responsabilité: Moustapha).
# Ce fichier contient la logique commune à TOUS les agents du système OMEGA.
# 1. Configuration du modèle LLM (Ollama, OpenAI, Anthropic, etc.).
# 2. Paramétrage des logs et du monitoring (Agentic UI, Tracing).
# 3. Définition d'une classe de base 'OmegaAgent' pour standardiser les interfaces.

from agno.agent import Agent
# from app.core.config import settings

class BaseOmegaAgent:
    """
    Classe parente pour garantir que tous les agents utilisent 
    la même configuration de modèle et les mêmes outils de debug.
    """
    def __init__(self, name: str, instructions: list):
        self.agent = Agent(
            name=name,
            instructions=instructions,
            # model=...,  # Configurer ici le modèle par défaut pour toute l'équipe
            markdown=True,
            show_tool_calls=True
        )

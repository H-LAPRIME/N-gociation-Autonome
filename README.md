# OMEGA : Système d'Orchestration Agentique

OMEGA est une plateforme backend robuste basée sur **FastAPI** et le framework **Agno**, conçue pour automatiser les cycles de négociation de véhicules via une architecture multi-agents.

## 🚀 Équipe & Rôles

Le projet est divisé en 5 pôles de développement :

1.  **Moustapha** (`Moustapha_Tasks.md`) : Fondation FastAPI, Profilage Utilisateur & API Bancaire.
2.  **Reda** (`Reda_Tasks.md`) : Évaluation du véhicule (Valuation) & Scraper de données marché.
3.  **Mohammed** (`Mohammed_Tasks.md`) : Analyse du marché, Gestion des stocks SQL & Tendances.
4.  **Mouad** (`Mouad_Tasks.md`) : **Orchestrateur Central** & Intelligence de Négociation.
5.  **Halima** (`Halima_Tasks.md`) : Structuration de l'offre finale & Validation des contraintes Business.

## 🛠️ Structure du Projet

- `app/main.py` : Point d'entrée de l'API.
- `app/agents/` : Définition des comportements de chaque agent.
- `app/tools/` : Outils métiers (Scrapers, APIs, SQL).
- `app/core/` : Configuration globale et sécurité.

## ⚙️ Installation

1.  **Prérequis** : Python 3.9+ possessé.
2.  **Installation des dépendances** :
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configuration** : Copiez le fichier `.env.example` (à créer) vers `.env` et remplissez vos clés API.
4.  **Démarrage** :
    ```bash
    uvicorn app.main:app --reload
    ```

## 🧠 Workflow Agentique
Le système suit un cycle bidirectionnel :
`Utilisateur` -> `Orchestrateur` -> `Agents Spécialisés` -> `Négociation` -> `Offre` -> `RETOUR Orchestrateur` -> `Réponse Client`.

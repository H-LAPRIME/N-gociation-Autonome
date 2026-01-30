# OMEGA Backend - AI-Powered Car Negotiation Engine

The OMEGA backend is a Python-based FastAPI application that orchestrates a multi-agent system to handle complex car transaction workflows.

## 🧠 Agent Architecture

The system uses a collaborative multi-agent architecture where a central **Orchestrator** coordinates specialized agents:

1.  **OrchestratorAgent**: The "Brain" of OMEGA. It classifies user intent, manages session state, and triggers the appropriate agent pipeline.
2.  **UserProfileAgent**: Analyzes fiscal health (via Bank API simulation) and extracts customer preferences/sentiment.
3.  **MarketAnalysisAgent**: Analyzes real-time market trends and showroom stock (CSV-based) to provide strategic context.
4.  **ValuationAgent**: Appraises trade-in vehicles using a combination of web scraping (Moteur.ma) and Python logic.
5.  **NegotiationAgent**: Manages multi-turn price negotiations, making calculated concessions to reach a deal.

## 🛠️ Core Tools

-   **Bank API Simulation**: Mock service providing user financial profiles.
-   **Car Market Scraper**: Aggressive caching scraper for real-time Moroccan car prices.
-   **Inventory Manager**: Handles local stock using `cars_market.csv`.
-   **PDF Generator**: Generates professional transaction contracts with QR codes.

## 🚀 Setup & Execution

1.  **Environment**: Create a `.env` file with necessary keys (LLM API keys, etc.).
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run Server**:
    ```bash
    uvicorn app.main:app --reload
    ```

## 📡 API Endpoints

-   `POST /auth/signup`: User registration.
-   `POST /auth/login`: Authentication and JWT generation.
-   `POST /orchestrate`: Central entry point for AI communication.
-   `GET /v1/market/statistics`: Real-time market data.
-   `POST /negotiation/start`: Initialize a new negotiation session.

/**
 * Market Service
 * --------------
 * Handles all market-related API calls, including statistics,
 * brand lists, and price evolution chart data.
 */
'use client';

/**
 * Chat Service
 * ------------
 * Manages chat sessions, listing historical conversations,
 * and deleting sessions via the backend API.
 */
import api from './api';

export interface MarketData {
    inventory: {
        avg_market_price: number;
        min_price: number;
        max_price: number;
        avg_mileage: number;
        stock_available: number;
    };
    market_trends: {
        trend_direction: 'up' | 'down';
        demand_score: number;
        demand_level: string;
    };
}

class MarketService {
    async getMarketTrends(model: string): Promise<{ result: MarketData }> {
        try {
            // Essayer d'obtenir les stats pour le modèle spécifique
            const endpoint = model && model.trim()
                ? `/v1/market/statistics/${encodeURIComponent(model)}`
                : '/v1/market/statistics';

            const response = await api.get(endpoint);

            if (!response?.data) {
                throw new Error('Aucune donnée reçue du serveur');
            }

            const data = response.data;
            const marketData: MarketData = {
                inventory: {
                    avg_market_price: data.avg_price || 0,
                    min_price: data.min_price || 0,
                    max_price: data.max_price || 0,
                    avg_mileage: data.avg_mileage || 0,
                    stock_available: data.total_vehicles || 0
                },
                market_trends: {
                    trend_direction: data.trend === 'up' ? 'up' : 'down',
                    demand_score: data.demand_score || 0,
                    demand_level: this._getDemandLevel(data.demand_score || 0)
                }
            };

            return { result: marketData };
        } catch (error: any) {
            console.error('[marketService] Error:', error);
            throw new Error(error.response?.data?.detail || 'Impossible de récupérer les données du marché');
        }
    }

    async getBrands(): Promise<string[]> {
        try {
            const response = await api.get('/v1/market/brands').catch(() => null);
            if (response?.data?.brands) {
                return response.data.brands;
            }
            return [];
        } catch (error) {
            console.error('[marketService] Error fetching brands:', error);
            return [];
        }
    }

    async getChartData(model: string): Promise<Array<{ month: string; price: number }>> {
        try {
            if (!model) return [];

            const response = await api.get(`/v1/market/chart/${encodeURIComponent(model)}`);
            if (response?.data && Array.isArray(response.data)) {
                return response.data;
            }
            return [];
        } catch (error) {
            console.error('[marketService] Chart error:', error);
            return [];
        }
    }

    private _getDemandLevel(score: number): string {
        if (score === 0) return 'Indisponible';
        if (score > 80) return 'Très Élevée';
        if (score > 60) return 'Élevée';
        if (score > 40) return 'Modérée';
        return 'Faible';
    }
}

export const marketService = new MarketService();

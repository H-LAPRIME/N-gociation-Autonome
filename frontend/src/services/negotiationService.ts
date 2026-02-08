/**
 * Negotiation Service
 * -------------------
 * Provides functions to start new negotiations, send messages/offers,
 * and retrieve negotiation history.
 */
import api from './api';

export interface NegotiationMessageRequest {
    message: string;
    counter_offer?: {
        desired_price: number;
        desired_monthly?: number;
    };
    action: 'accept' | 'reject' | 'counter';
}

export interface NegotiationMessageResponse {
    agent_response: string;
    revised_offer?: any;
    round: number;
    remaining_rounds: number;
    status: string;
    session_id: string;
    validation_info?: {
        is_approved: boolean;
        audit_trail: string[];
        violations: string[];
        confidence_score: number;
    };
}

export interface NegotiationHistory {
    id: number;
    session_id: string;
    round_number: number;
    speaker: string;
    message: string;
    offer_data?: any;
    action: string;
    timestamp: string;
}

export const negotiationService = {
    start: async (data: any) => {
        const response = await api.post('/negotiation/start', data);
        return response.data;
    },

    sendMessage: async (sessionId: string, data: NegotiationMessageRequest): Promise<NegotiationMessageResponse> => {
        const response = await api.post(`/negotiation/${sessionId}/message`, data);
        return response.data;
    },

    getHistory: async (sessionId: string): Promise<NegotiationHistory[]> => {
        const response = await api.get(`/negotiation/${sessionId}/history`);
        return response.data;
    },

    getSession: async (sessionId: string) => {
        const response = await api.get(`/negotiation/${sessionId}`);
        return response.data;
    },

    resetSession: async (sessionId: string) => {
        const response = await api.delete(`/negotiation/${sessionId}`);
        return response.data;
    }
};

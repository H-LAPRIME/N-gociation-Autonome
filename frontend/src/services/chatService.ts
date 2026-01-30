/**
 * Chat Service
 * ------------
 * Manages chat sessions, listing historical conversations,
 * and deleting sessions via the backend API.
 */
import api from './api';

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
}

export interface ChatSession {
    session_id: string;
    user_id: number;
    title: string;
    messages: ChatMessage[];
    created_at: string;
    updated_at: string;
    profile_state: any;
}

export const chatService = {
    async createSession(): Promise<ChatSession> {
        const response = await api.post('/chat/sessions');
        return response.data;
    },

    async listSessions(): Promise<ChatSession[]> {
        const response = await api.get('/chat/sessions');
        return response.data;
    },

    async getSession(sessionId: string): Promise<ChatSession> {
        const response = await api.get(`/chat/sessions/${sessionId}`);
        return response.data;
    },

    async deleteSession(sessionId: string): Promise<{ success: boolean }> {
        const response = await api.delete(`/chat/sessions/${sessionId}`);
        return response.data;
    }
};

import api from './api';

export interface OrchestrateRequest {
    query: string;
    history: Array<{ role: string; content: string }>;
    user_profile_state: Record<string, any>;
    session_id?: string;
}

export interface OrchestrateResponse {
    chat_response: string;
    profile_data_extracted?: Record<string, any>;
    ui_action?: any;
    [key: string]: any; // Allow for other fields
}

export const orchestratorService = {
    orchestrate: async (data: OrchestrateRequest): Promise<OrchestrateResponse> => {
        const response = await api.post('/orchestrate', data);
        return response.data;
    },
};


import api from './api';

export interface UserProfileData {
    user_id: number;
    username: string;
    email: string;
    full_name: string;
    city?: string;
    income_mad?: number;
    risk_level?: string;
    preferences?: any;
    financials?: any;
    trade_in?: any;
}

export interface AnalyzeProfileRequest {
    user_id: number;
    user_input: Record<string, any>;
}

export const userService = {
    getUserProfile: async (): Promise<UserProfileData> => {
        const response = await api.get('/user/profile');
        return response.data;
    },

    analyzeUserProfile: async (data: AnalyzeProfileRequest) => {
        const response = await api.post('/user/analyze', data);
        return response.data;
    },

    updateUserProfile: async (data: Partial<UserProfileData>) => {
        const response = await api.put('/user/profile', data);
        return response.data;
    },
};

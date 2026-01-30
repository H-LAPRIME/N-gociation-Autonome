/**
 * Auth Context
 * ------------
 * Manages user authentication state, including login, signup,
 * token persistence, and logout flow.
 */
'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '@/services/api';

interface User {
    user_id: number;
    email: string;
    full_name: string;
    city?: string;
    income_mad?: number;
}

interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    login: (email: string, pass: string) => Promise<void>;
    signup: (data: any) => Promise<void>;
    logout: () => void;
    updateUser: (data: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const savedUser = localStorage.getItem('omega_user');
        const token = localStorage.getItem('access_token');
        if (savedUser && token) {
            setUser(JSON.parse(savedUser));
        }
        setIsLoading(false);
    }, []);

    const login = async (email: string, pass: string) => {
        setIsLoading(true);
        try {
            const response = await api.post('/auth/login', { email, password: pass });
            if (response.data.success) {
                const authenticatedUser = response.data.user;
                const token = response.data.access_token;

                setUser(authenticatedUser);
                localStorage.setItem('omega_user', JSON.stringify(authenticatedUser));
                localStorage.setItem('access_token', token);
            }
        } catch (error: any) {
            const detail = error.response?.data?.detail;
            const message = typeof detail === 'string' ? detail : (Array.isArray(detail) ? detail[0]?.msg : 'Identifiants invalides');
            console.error("Login failed", error);
            throw new Error(message);
        } finally {
            setIsLoading(false);
        }
    };

    const signup = async (data: any) => {
        setIsLoading(true);
        try {
            const response = await api.post('/auth/signup', data);
            if (response.data.success) {
                const newUser = response.data.user;
                const token = response.data.access_token;

                setUser(newUser);
                localStorage.setItem('omega_user', JSON.stringify(newUser));
                localStorage.setItem('access_token', token);
            }
        } catch (error: any) {
            const detail = error.response?.data?.detail;
            // Handle FastAPI validation errors which are often in detail list
            const message = typeof detail === 'string' ? detail : (Array.isArray(detail) ? `Erreur: ${detail[0]?.msg || 'Données invalides'}` : 'Une erreur est survenue lors de l\'inscription.');
            console.error("Signup failed", error);
            throw new Error(message);
        } finally {
            setIsLoading(false);
        }
    };

    const logout = () => {
        setUser(null);
        localStorage.removeItem('omega_user');
        localStorage.removeItem('access_token');
    };

    const updateUser = (data: Partial<User>) => {
        if (!user) return;
        const updatedUser = { ...user, ...data };
        setUser(updatedUser);
        localStorage.setItem('omega_user', JSON.stringify(updatedUser));
    };

    return (
        <AuthContext.Provider value={{ user, isLoading, login, signup, logout, updateUser }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}


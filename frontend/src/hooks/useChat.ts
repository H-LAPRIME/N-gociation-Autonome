/**
 * useChat Hook
 * ------------
 * The primary hook for managing the complex chat and negotiation state.
 * Handles message sending, state orchestration, negotiation triggers,
 * and UI actions (forms, cards, etc.).
 */
import { useState, useCallback, useEffect } from 'react';
import { orchestratorService } from '@/services/orchestratorService';
import { negotiationService } from '@/services/negotiationService';
import { chatService, ChatSession, ChatMessage as ServerChatMessage } from '@/services/chatService';

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: number;
}

export interface ChatState {
    messages: Message[];
    isLoading: boolean;
    profileState: Record<string, any>;
}

export function useChat() {
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
    const [messages, setMessages] = useState<Message[]>([
        {
            id: 'welcome',
            role: 'assistant',
            content: 'Bonjour ! Je suis OMEGA. Comment puis-je vous aider dans votre projet automobile aujourd\'hui ?',
            timestamp: Date.now(),
        },
    ]);
    const [isLoading, setIsLoading] = useState(false);
    const [profileState, setProfileState] = useState<Record<string, any>>({});
    const [uiAction, setUiAction] = useState<any>(null);

    // Negotiation State
    const [negotiationState, setNegotiationState] = useState<any>(null);

    const loadSessions = useCallback(async () => {
        try {
            const list = await chatService.listSessions();
            setSessions(list);

            // If no current session, try to load latest
            if (!currentSessionId && list.length > 0) {
                // Optional: auto-load latest session
                // selectSession(list[0].session_id);
            }
        } catch (error) {
            console.error('Failed to load sessions:', error);
        }
    }, [currentSessionId]);

    useEffect(() => {
        loadSessions();
    }, []);

    const selectSession = useCallback(async (sessionId: string) => {
        setIsLoading(true);
        try {
            const session = await chatService.getSession(sessionId);
            setCurrentSessionId(session.session_id);

            if (session.messages && session.messages.length > 0) {
                setMessages(session.messages.map(m => ({
                    id: m.id,
                    role: m.role as 'user' | 'assistant',
                    content: m.content,
                    timestamp: new Date(m.timestamp).getTime()
                })));
            } else {
                setMessages([
                    {
                        id: 'welcome',
                        role: 'assistant',
                        content: 'Bonjour ! Je suis OMEGA. Comment puis-je vous aider dans votre projet automobile aujourd\'hui ?',
                        timestamp: Date.now(),
                    }
                ]);
            }
            setProfileState(session.profile_state || {});
            setNegotiationState(null);
            setUiAction(null);
        } catch (error) {
            console.error('Failed to load session:', error);
        } finally {
            setIsLoading(false);
        }
    }, []);

    const createNewSession = useCallback(async () => {
        setIsLoading(true);
        try {
            const newSession = await chatService.createSession();
            setSessions(prev => [newSession, ...prev]);
            setCurrentSessionId(newSession.session_id);
            setMessages([
                {
                    id: 'welcome',
                    role: 'assistant',
                    content: 'Bonjour ! Je suis OMEGA. Comment puis-je vous aider dans votre projet automobile aujourd\'hui ?',
                    timestamp: Date.now(),
                }
            ]);
            setProfileState({});
            setNegotiationState(null);
            setUiAction(null);
        } catch (error) {
            console.error('Failed to create session:', error);
        } finally {
            setIsLoading(false);
        }
    }, []);

    const deleteSession = useCallback(async (sessionId: string) => {
        try {
            await chatService.deleteSession(sessionId);
            setSessions(prev => prev.filter(s => s.session_id !== sessionId));
            if (currentSessionId === sessionId) {
                setCurrentSessionId(null);
                setMessages([
                    {
                        id: 'welcome',
                        role: 'assistant',
                        content: 'Bonjour ! Je suis OMEGA. Comment puis-je vous aider dans votre projet automobile aujourd\'hui ?',
                        timestamp: Date.now(),
                    }
                ]);
                setProfileState({});
            }
        } catch (error) {
            console.error('Failed to delete session:', error);
        }
    }, [currentSessionId]);

    const updateProfileState = useCallback((extractedData: any) => {
        if (!extractedData) return;

        setProfileState((prev) => {
            const newState = { ...prev };

            // Deep merge profil_extraction if it exists
            if (extractedData.profil_extraction) {
                newState.profil_extraction = {
                    ...(prev.profil_extraction || {}),
                    ...extractedData.profil_extraction
                };
            }

            // Merge other top-level fields
            const { profil_extraction, ...others } = extractedData;
            return {
                ...newState,
                ...others
            };
        });
    }, []);

    const sendMessage = useCallback(async (content: string) => {
        if (!content.trim()) return;

        // If no session active, create one first or show error
        let sessionId = currentSessionId;
        if (!sessionId) {
            try {
                const newSession = await chatService.createSession();
                setSessions(prev => [newSession, ...prev]);
                setCurrentSessionId(newSession.session_id);
                sessionId = newSession.session_id;
            } catch (error) {
                console.error("Failed to auto-create session", error);
                return;
            }
        }

        // Add user message
        const userMsg: Message = {
            id: Date.now().toString(),
            role: 'user',
            content,
            timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, userMsg]);
        setIsLoading(true);

        try {
            // Prepare history for backend (last 10 messages)
            const history = messages.slice(-10).map((m) => ({
                role: m.role,
                content: m.content,
            }));

            const data = await orchestratorService.orchestrate({
                query: content,
                history,
                user_profile_state: profileState,
                session_id: sessionId || undefined
            });


            if (data.chat_response) {
                const botMsg: Message = {
                    id: (Date.now() + 1).toString(),
                    role: 'assistant',
                    content: data.chat_response,
                    timestamp: Date.now(),
                };
                setMessages((prev) => [...prev, botMsg]);
            }

            // Update profile state if returned
            if (data.profile_data_extracted) {
                updateProfileState(data.profile_data_extracted);
            }

            // Handle UI Actions (e.g., showing a form)
            if (data.ui_action) {
                setUiAction(data.ui_action);

                // Special handling for negotiation start
                if (data.ui_action.type === 'START_NEGOTIATION') {
                    setNegotiationState({
                        sessionId: data.ui_action.session_id,
                        initialOffer: data.ui_action.initial_offer,
                        maxRounds: data.ui_action.max_rounds,
                        currentRound: data.ui_action.current_round
                    });
                }
            }

        } catch (error) {
            console.error('Chat error:', error);
            const errorMsg: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: "Désolé, une erreur est survenue. Veuillez réessayer.",
                timestamp: Date.now(),
            };
            setMessages((prev) => [...prev, errorMsg]);
        } finally {
            setIsLoading(false);
        }
    }, [messages, profileState, updateProfileState, currentSessionId]);

    const clearUiAction = useCallback(() => setUiAction(null), []);

    const submitTradeIn = useCallback(async (tradeInData: any) => {
        if (!currentSessionId) return;

        // Generate a friendly summary message for the UI
        const userSummary = `Je souhaite faire une reprise pour mon véhicule : **${tradeInData.brand} ${tradeInData.model}** de **${tradeInData.year}** (${tradeInData.mileage.toLocaleString()} km, état ${tradeInData.condition}).`;

        // Add user summary message to UI
        const userMsg: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: userSummary,
            timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, userMsg]);

        // Technical query for backend orchestration
        const autoNegotiateQuery = `[AUTO_NEGOTIATE] Client veut acheter. Profil: ${JSON.stringify(profileState)} | Reprise: ${JSON.stringify(tradeInData)}`;

        // Clear the UI action (close the modal)
        setUiAction(null);

        // Set loading state
        setIsLoading(true);

        try {
            // Prepare history for backend (last 10 messages)
            const history = messages.slice(-10).map((m) => ({
                role: m.role,
                content: m.content,
            }));

            // Send directly to backend
            const data = await orchestratorService.orchestrate({
                query: autoNegotiateQuery,
                history,
                user_profile_state: profileState,
                session_id: currentSessionId
            });

            // Show the bot's response
            if (data.chat_response) {
                const botMsg: Message = {
                    id: (Date.now() + 1).toString(),
                    role: 'assistant',
                    content: data.chat_response,
                    timestamp: Date.now(),
                };
                setMessages((prev) => [...prev, botMsg]);
            }

            // Update profile state if returned
            if (data.profile_data_extracted) {
                updateProfileState(data.profile_data_extracted);
            }

            // Handle UI Actions
            if (data.ui_action) {
                setUiAction(data.ui_action);

                // Special handling for negotiation start
                if (data.ui_action.type === 'START_NEGOTIATION') {
                    setNegotiationState({
                        sessionId: data.ui_action.session_id,
                        initialOffer: data.ui_action.initial_offer,
                        maxRounds: data.ui_action.max_rounds,
                        currentRound: data.ui_action.current_round
                    });
                }
            }

        } catch (error) {
            console.error('Trade-in submission error:', error);
            const errorMsg: Message = {
                id: Date.now().toString(),
                role: 'assistant',
                content: "Désolé, une erreur est survenue lors de l'estimation. Veuillez réessayer.",
                timestamp: Date.now(),
            };
            setMessages((prev) => [...prev, errorMsg]);
        } finally {
            setIsLoading(false);
        }
    }, [profileState, messages, updateProfileState, currentSessionId]);

    const handleNegotiationUpdate = useCallback((message: any) => {
        const botMsg: Message = {
            id: Date.now().toString(),
            role: 'assistant',
            content: message.content,
            timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, botMsg]);
    }, []);

    const handleNegotiationReset = useCallback(async () => {
        if (!negotiationState) return;
        try {
            await negotiationService.resetSession(negotiationState.sessionId);
            setNegotiationState(null);

            const botMsg: Message = {
                id: Date.now().toString(),
                role: 'assistant',
                content: "La négociation a été réinitialisée. Vous pouvez commencer une nouvelle demande quand vous voulez.",
                timestamp: Date.now(),
            };
            setMessages((prev) => [...prev, botMsg]);

        } catch (error) {
            console.error("Failed to reset session", error);
        }
    }, [negotiationState]);

    return {
        messages,
        isLoading,
        sendMessage,
        submitTradeIn,
        uiAction,
        clearUiAction,
        profileState,
        negotiationState,
        handleNegotiationUpdate,
        handleNegotiationReset,
        sessions,
        currentSessionId,
        selectSession,
        createNewSession,
        deleteSession
    };
}

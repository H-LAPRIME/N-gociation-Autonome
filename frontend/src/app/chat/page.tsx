/**
 * Chat Page
 * ---------
 * The main interactive interface for OMEGA.
 * Features a persistent sidebar for conversation history and a premium 
 * chat area with integrated negotiation cards and trade-in modals.
 */
'use client';

import { useEffect, useRef, useState } from 'react';
import {
    Send, Bot, User, Loader2, Info, Sparkles, Zap, Shield,
    MessageCircle, Plus, History, Trash2, ChevronLeft, ChevronRight, X
} from 'lucide-react';
import { useChat } from '@/hooks/useChat';
import { TradeInModal } from '@/components/chat/TradeInModal';
import { NegotiationCard } from '@/components/chat/NegotiationCard';
import { AnimatePresence, motion } from 'framer-motion';
import { GlassCard } from '@/components/UI/GlassCard';
import Navbar from '@/components/Navbar/Navbar';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

// Utility for formatting messages (both User and Assistant)
const formatMessage = (content: string, role: 'user' | 'assistant') => {
    // Replace **word** with <strong class="...">WORD</strong>
    let formatted = content.replace(/\*\*([^*]+)\*\*/g, (match, word) => {
        const colorClass = role === 'user' ? 'text-white' : 'text-blue-400';
        return `<strong class="${colorClass} font-bold">${word.toUpperCase()}</strong>`;
    });

    // Add line breaks after ":" and "." if followed by space OR end of string
    // This makes the text much more readable and premium
    formatted = formatted.replace(/([.:])(\s+|$)/g, '$1<br/><br/>');

    return formatted;
};

export default function ChatPage() {
    const {
        messages,
        isLoading,
        sendMessage,
        submitTradeIn,
        uiAction,
        clearUiAction,
        negotiationState,
        handleNegotiationUpdate,
        handleNegotiationReset,
        sessions,
        currentSessionId,
        selectSession,
        createNewSession,
        deleteSession
    } = useChat();

    const [input, setInput] = useState('');
    const [mounted, setMounted] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        setMounted(true);
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages, isLoading]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;
        sendMessage(input);
        setInput('');
    };

    if (!mounted) return null;

    const chatAreaContent = (
        <main className="flex-1 overflow-hidden pt-20 flex flex-col relative min-w-0">
            {/* Premium Animated Nebula Background */}
            <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
                <div className="absolute -top-[10%] -left-[10%] w-[70%] h-[70%] bg-blue-600/15 rounded-full blur-[120px] animate-drift" />
                <div className="absolute top-[20%] -right-[5%] w-[60%] h-[60%] bg-purple-600/10 rounded-full blur-[140px] animate-drift" style={{ animationDelay: '-5s' }} />
                <div className="absolute -bottom-[20%] left-[20%] w-[80%] h-[80%] bg-blue-900/10 rounded-full blur-[160px] animate-drift" style={{ animationDelay: '-10s' }} />
                <div className="absolute top-1/4 right-1/4 w-[40%] h-[40%] bg-blue-400/5 rounded-full blur-[100px] animate-pulse" />
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-[#020205] -z-10" />
            </div>

            <div className="container mx-auto max-w-5xl flex-1 flex flex-col overflow-hidden px-4 relative z-10">
                {/* Premium Header */}
                <div className="flex items-center justify-between py-6 border-b border-white/5">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => setSidebarOpen(!sidebarOpen)}
                            className="p-2 rounded-xl bg-white/5 border border-white/10 text-white/40 hover:text-white transition-colors lg:hidden"
                        >
                            <History size={20} />
                        </button>
                        <div className="flex items-center gap-4">
                            <div className="relative">
                                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-600 to-blue-400 flex items-center justify-center shadow-lg shadow-blue-500/20">
                                    <Bot className="text-white w-7 h-7" />
                                </div>
                                <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-green-500 border-2 border-[#050505] flex items-center justify-center">
                                    <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                                </div>
                            </div>
                            <div>
                                <h1 className="text-white text-lg font-bold tracking-tight flex items-center gap-2">
                                    OMEGA Intelligence
                                    <span className="px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-[10px] text-blue-400 font-mono uppercase tracking-tighter">v2.0</span>
                                </h1>
                                <p className="text-white/40 text-xs flex items-center gap-1.5 mt-0.5 font-medium uppercase tracking-widest">
                                    <Zap size={10} className="text-amber-400" />
                                    Prêt pour la négociation
                                </p>
                            </div>
                        </div>
                    </div>
                    <div className="hidden md:flex items-center gap-3">
                        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/5 border border-white/10">
                            <Shield className="text-blue-400 w-3.5 h-3.5" />
                            <span className="text-[10px] text-white/60 font-bold tracking-wider uppercase">Chiffrement AES-256</span>
                        </div>
                        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-500/10 border border-blue-500/20">
                            <Sparkles className="text-amber-400 w-3.5 h-3.5" />
                            <span className="text-[10px] text-blue-400 font-bold tracking-wider uppercase">IA Analyse active</span>
                        </div>
                    </div>
                </div>

                {/* Chat Messages Container */}
                <div className="flex-1 overflow-y-auto py-8 custom-scrollbar space-y-8 px-2 scroll-smooth">
                    <AnimatePresence initial={false}>
                        {messages.map((m, index) => (
                            <motion.div
                                key={m.id}
                                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
                                className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                                <div className={`flex gap-4 max-w-[85%] md:max-w-[75%] ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
                                    <div className={`w-9 h-9 rounded-xl flex-shrink-0 flex items-center justify-center border shadow-xl ${m.role === 'user'
                                        ? 'bg-blue-600 border-blue-500 shadow-blue-500/20'
                                        : 'bg-[#121212] border-white/10 shadow-black/50'
                                        }`}>
                                        {m.role === 'user' ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-blue-400" />}
                                    </div>
                                    <div className="flex flex-col gap-1">
                                        <div className={`relative px-6 py-4 rounded-3xl text-[15px] leading-[1.6] shadow-2xl backdrop-blur-md ${m.role === 'user'
                                            ? 'bg-blue-600 text-white rounded-tr-none shadow-lg shadow-blue-500/20'
                                            : 'bg-white/5 text-gray-200 border border-white/10 rounded-tl-none font-medium'
                                            }`}>
                                            {/* Bubble Glow for Assistant */}
                                            {m.role === 'assistant' && (
                                                <div className="absolute -inset-0.5 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-3xl blur-[10px] -z-10 opacity-50" />
                                            )}

                                            {m.role === 'user' ? (
                                                <div
                                                    className="prose prose-invert max-w-none text-white font-medium"
                                                    dangerouslySetInnerHTML={{ __html: formatMessage(m.content, 'user').replace(/\n/g, '<br />') }}
                                                />
                                            ) : index === 0 ? (
                                                /* Special rendering for welcome message */
                                                <div className="space-y-4">
                                                    <p className="text-lg font-bold">Bonjour ! <span aria-hidden>👋</span></p>
                                                    <p>Je suis <strong className="text-blue-400">OMEGA</strong>, votre expert IA personnel pour ce showroom automobile.</p>
                                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4">
                                                        <div className="p-3 rounded-2xl bg-white/5 border border-white/10 hover:border-blue-500/30 transition-colors cursor-pointer group/card border-transparent">
                                                            <Zap className="w-4 h-4 text-amber-400 mb-2" />
                                                            <p className="text-xs font-bold text-white mb-1">Reprise Express</p>
                                                            <p className="text-[10px] text-white/40 leading-relaxed">Estimez et négociez votre ancien véhicule en 2 minutes.</p>
                                                        </div>
                                                        <div className="p-3 rounded-2xl bg-white/5 border border-white/10 hover:border-blue-500/30 transition-colors cursor-pointer group/card border-transparent">
                                                            <MessageCircle className="w-4 h-4 text-blue-400 mb-2" />
                                                            <p className="text-xs font-bold text-white mb-1">Achat Intelligent</p>
                                                            <p className="text-[10px] text-white/40 leading-relaxed">Trouvez le financement parfait (Crédit, LLD, Abonnement).</p>
                                                        </div>
                                                    </div>
                                                </div>
                                            ) : (
                                                <div
                                                    className="prose prose-invert max-w-none"
                                                    dangerouslySetInnerHTML={{ __html: formatMessage(m.content, 'assistant').replace(/\n/g, '<br />') }}
                                                />
                                            )}
                                        </div>
                                        <div className={`flex items-center gap-2 px-2 text-[9px] font-bold uppercase tracking-widest opacity-30 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
                                            <span>{new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                            <div className="w-0.5 h-0.5 rounded-full bg-white" />
                                            <span>{m.role === 'assistant' ? 'AI Agent' : 'Auth Client'}</span>
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>

                    {isLoading && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex justify-start"
                        >
                            <div className="flex gap-4 items-center bg-white/5 px-6 py-4 rounded-3xl border border-white/10 backdrop-blur-lg">
                                <div className="flex gap-1.5">
                                    <motion.span
                                        animate={{ opacity: [0.3, 1, 0.3], scale: [1, 1.2, 1] }}
                                        transition={{ duration: 1.5, repeat: Infinity }}
                                        className="w-2 h-2 bg-blue-400 rounded-full"
                                    />
                                    <motion.span
                                        animate={{ opacity: [0.3, 1, 0.3], scale: [1, 1.2, 1] }}
                                        transition={{ duration: 1.5, repeat: Infinity, delay: 0.2 }}
                                        className="w-2 h-2 bg-blue-400 rounded-full"
                                    />
                                    <motion.span
                                        animate={{ opacity: [0.3, 1, 0.3], scale: [1, 1.2, 1] }}
                                        transition={{ duration: 1.5, repeat: Infinity, delay: 0.4 }}
                                        className="w-2 h-2 bg-blue-400 rounded-full"
                                    />
                                </div>
                                <span className="text-xs text-blue-300 font-bold uppercase tracking-[0.2em] animate-pulse">OMEGA analyse en temps réel...</span>
                            </div>
                        </motion.div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Negotiation Card Container with Glow */}
                {negotiationState && (
                    <motion.div
                        initial={{ opacity: 0, y: 40 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-4 relative"
                    >
                        <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-purple-600 rounded-[2rem] blur-xl opacity-20" />
                        <NegotiationCard
                            sessionId={negotiationState.sessionId}
                            initialOffer={negotiationState.initialOffer}
                            maxRounds={negotiationState.maxRounds}
                            currentRound={negotiationState.currentRound}
                            onNegotiationUpdate={handleNegotiationUpdate}
                            onReset={handleNegotiationReset}
                        />
                    </motion.div>
                )}

                {/* Premium Input Area */}
                <div className="pb-8 pt-4">
                    <form onSubmit={handleSubmit} className="relative group">
                        <div className="absolute -inset-1 bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-[2.5rem] blur-2xl group-focus-within:opacity-100 opacity-0 transition-opacity duration-700" />

                        <div className="relative flex items-center gap-3 bg-[#111111]/90 backdrop-blur-2xl border border-white/10 rounded-3xl p-3 focus-within:border-blue-500/50 focus-within:ring-4 focus-within:ring-blue-500/5 transition-all duration-500 shadow-[0_20px_50px_rgba(0,0,0,0.5)]">
                            <div className="hidden sm:flex items-center justify-center w-12 h-12 rounded-2xl bg-white/5 border border-white/10 text-white/40">
                                <Sparkles className="w-5 h-5" />
                            </div>

                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Posez votre question ou proposez un prix..."
                                className="flex-1 bg-transparent border-none focus:ring-0 text-white px-2 py-3 placeholder:text-white/20 text-[15px] font-medium"
                                disabled={isLoading}
                            />

                            <button
                                type="submit"
                                disabled={!input.trim() || isLoading}
                                className={`relative flex items-center justify-center w-14 h-14 rounded-2xl transition-all duration-500 overflow-hidden ${!input.trim() || isLoading
                                    ? 'bg-white/5 text-white/10'
                                    : 'bg-blue-600 text-white shadow-[0_0_30px_rgba(37,99,235,0.4)] hover:scale-105 active:scale-95 group/btn'
                                    }`}
                            >
                                {isLoading ? (
                                    <Loader2 className="w-6 h-6 animate-spin" />
                                ) : (
                                    <>
                                        <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent opacity-0 group-hover/btn:opacity-100 transition-opacity" />
                                        <Send className="w-6 h-6 relative z-10" />
                                    </>
                                )}
                            </button>
                        </div>

                        {/* Utility Toolbar */}
                        <div className="flex justify-between mt-4 px-4">
                            <div className="flex items-center gap-6">
                                <p className="text-[10px] text-white/20 font-bold uppercase tracking-widest flex items-center gap-2">
                                    <Info className="w-3.5 h-3.5 text-blue-400" />
                                    Appuyez sur Entrée
                                </p>
                                <div className="h-4 w-px bg-white/5" />
                                <button type="button" className="text-[10px] text-white/20 hover:text-blue-400 font-bold uppercase tracking-widest transition-colors flex items-center gap-1.5">
                                    <MessageCircle className="w-2.5 h-2.5" />
                                    Suggestions
                                </button>
                            </div>
                            <div className="flex gap-6">
                                <button
                                    type="button"
                                    onClick={() => sendMessage("[AUTO_NEGOTIATE] Force restart")}
                                    className="text-[10px] text-white/20 hover:text-blue-400 font-bold uppercase tracking-widest transition-colors"
                                >
                                    Relancer
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setInput('')}
                                    className="text-[10px] text-white/20 hover:text-red-400 font-bold uppercase tracking-widest transition-colors"
                                >
                                    Effacer
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </main>
    );

    const sidebarContent = (
        <div className={`fixed inset-y-0 left-0 lg:relative z-[60] flex transition-all duration-300 ${sidebarOpen ? 'w-80' : 'w-0'}`}>
            <aside className="h-full w-full bg-[#080808] border-r border-white/5 flex flex-col overflow-hidden relative">
                <div className="p-6 flex flex-col h-full min-w-[20rem]">
                    <button
                        onClick={createNewSession}
                        className="w-full py-4 px-6 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-blue-500/30 transition-all flex items-center justify-center gap-3 group mb-8 mb-8"
                    >
                        <Plus size={18} className="text-blue-400 group-hover:scale-110 transition-transform" />
                        <span className="text-sm font-bold text-white/80">Nouvelle Discussion</span>
                    </button>

                    <div className="flex-1 overflow-y-auto custom-scrollbar space-y-4 pr-2">
                        <div className="flex items-center gap-2 mb-4 px-2">
                            <History size={14} className="text-white/20" />
                            <span className="text-[10px] text-white/20 font-bold uppercase tracking-widest">Historique Récent</span>
                        </div>

                        {sessions.map((session) => (
                            <div
                                key={session.session_id}
                                className={`group relative p-4 rounded-2xl transition-all cursor-pointer border ${currentSessionId === session.session_id
                                    ? 'bg-blue-600/10 border-blue-500/30 ring-1 ring-blue-500/20'
                                    : 'bg-white/[0.02] border-white/5 hover:bg-white/5 hover:border-white/10'
                                    }`}
                                onClick={() => selectSession(session.session_id)}
                            >
                                <div className="flex items-start justify-between gap-3">
                                    <div className="flex-1 min-w-0">
                                        <h3 className={`text-sm font-bold truncate ${currentSessionId === session.session_id ? 'text-blue-400' : 'text-white/70'
                                            }`}>
                                            {session.title || "Nouvelle conversation"}
                                        </h3>
                                        <p className="text-[10px] text-white/30 mt-1 font-medium italic">
                                            {new Date(session.updated_at).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                                        </p>
                                    </div>
                                    <button
                                        onClick={(e) => { e.stopPropagation(); deleteSession(session.session_id); }}
                                        className="opacity-0 group-hover:opacity-100 p-2 rounded-lg hover:bg-red-500/10 text-white/20 hover:text-red-400 transition-all"
                                    >
                                        <Trash2 size={14} />
                                    </button>
                                </div>
                            </div>
                        ))}

                        {sessions.length === 0 && (
                            <div className="flex flex-col items-center justify-center py-20 text-center px-6">
                                <div className="w-12 h-12 rounded-2xl bg-white/5 flex items-center justify-center mb-4">
                                    <MessageCircle className="text-white/10 w-6 h-6" />
                                </div>
                                <p className="text-xs text-white/20 font-medium leading-relaxed">
                                    Aucune discussion trouvée.<br />Commencez votre première expérience avec OMEGA.
                                </p>
                            </div>
                        )}
                    </div>

                    <div className="mt-8 pt-6 border-t border-white/5">
                        <div className="flex items-center gap-3 p-3 rounded-2xl bg-white/[0.02] border border-white/5">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600/20 to-blue-400/20 flex items-center justify-center">
                                <User className="text-blue-400 w-5 h-5" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-xs font-bold text-white/80 truncate">Session Utilisateur</p>
                                <p className="text-[9px] text-white/30 font-bold uppercase tracking-tighter">Client Premium</p>
                            </div>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Sidebar Toggle Handle (Desktop) */}
            <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className={`absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-12 bg-[#080808] border border-white/5 rounded-full z-[70] hidden lg:flex items-center justify-center text-white/40 hover:text-white transition-colors group shadow-2xl ${!sidebarOpen ? 'translate-x-0' : ''}`}
            >
                {sidebarOpen ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
            </button>

            {/* Mobile Sidebar Close Button */}
            {sidebarOpen && (
                <button
                    onClick={() => setSidebarOpen(false)}
                    className="absolute top-6 right-6 p-2 rounded-xl bg-white/5 text-white lg:hidden z-50"
                >
                    <X size={20} />
                </button>
            )}
        </div>
    );

    return (
        <ProtectedRoute>
            <div className="flex h-screen bg-[#020205]/95 overflow-hidden">
                {sidebarContent}
                <div className="flex-1 flex flex-col overflow-hidden relative">
                    <Navbar />
                    {chatAreaContent}
                </div>

                {/* Premium Modals */}
                <AnimatePresence>
                    {uiAction?.type === 'SHOW_TRADE_IN' && (
                        <TradeInModal
                            isOpen={true}
                            onClose={clearUiAction}
                            onSubmit={submitTradeIn}
                        />
                    )}
                </AnimatePresence>
            </div>
        </ProtectedRoute>
    );
}

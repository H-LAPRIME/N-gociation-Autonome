'use client';

import React from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { motion } from 'framer-motion';
import { LogOut, MessageSquare, Menu, X } from 'lucide-react';
import { useState } from 'react';

export default function Navbar() {
    const { user, logout } = useAuth();
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-4 pointer-events-none">
            <div className="max-w-7xl mx-auto flex items-center justify-between pointer-events-auto px-6 py-3 rounded-2xl glass border border-white/5 bg-black/20 backdrop-blur-xl shadow-2xl">
                <Link href="/" className="flex items-center gap-2 group">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center group-hover:rotate-12 transition-transform">
                        <span className="text-white font-bold text-xl">Ω</span>
                    </div>
                    <span className="text-xl font-bold tracking-tight gradient-text">OMEGA</span>
                </Link>

                {/* Desktop Nav */}
                <div className="hidden md:flex items-center gap-8">
                    <Link href="/" className="text-sm font-medium text-white/60 hover:text-white transition-colors">Accueil</Link>
                    {user && (
                        <Link href="/chat" className="text-sm font-medium text-white/60 hover:text-white transition-colors flex items-center gap-2">
                            <MessageSquare size={16} /> Chat
                        </Link>
                    )}
                </div>

                <div className="hidden md:flex items-center gap-4">
                    {user ? (
                        <>
                            <Link href="/dashboard" className="flex items-center gap-4 pl-4 border-l border-white/10 hover:bg-white/5 transition-colors rounded-xl py-1">
                                <div className="flex flex-col items-end mr-2">
                                    <span className="text-xs font-semibold text-white/90">{user?.full_name?.split(' ')[0] || 'Client'}</span>
                                    <span className="text-[10px] text-white/40 uppercase tracking-widest">Client Premium</span>
                                </div>
                            </Link>
                            <button
                                onClick={logout}
                                className="p-2 rounded-xl bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-all active:scale-95"
                                title="Se déconnecter"
                            >
                                <LogOut size={18} />
                            </button>
                        </>
                    ) : (
                        <>
                            <Link href="/login" className="text-sm font-semibold text-white/70 hover:text-white transition-colors pr-4">Se connecter</Link>
                            <Link
                                href="/signup"
                                className="px-5 py-2.5 rounded-xl bg-white text-black font-bold text-sm hover:bg-white/90 transition-all active:scale-95 shadow-lg shadow-white/10"
                            >
                                Commencer
                            </Link>
                        </>
                    )}
                </div>

                {/* Mobile Menu Toggle */}
                <button className="md:hidden text-white/80" onClick={() => setIsMenuOpen(!isMenuOpen)}>
                    {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
                </button>
            </div>

            {/* Mobile Menu (simplified for now) */}
            {isMenuOpen && (
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="md:hidden mt-2 p-6 rounded-2xl glass border border-white/10 bg-black/80 pointer-events-auto flex flex-col gap-4"
                >
                    <Link href="/" className="text-lg font-medium py-2 border-bottom border-white/5">Accueil</Link>
                    {user ? (
                        <>
                            <Link href="/chat" className="text-lg font-medium py-2">Chat</Link>
                            <button onClick={logout} className="text-lg font-medium py-2 text-red-400 text-left">Déconnexion</button>
                        </>
                    ) : (
                        <>
                            <Link href="/login" className="text-lg font-medium py-2">Se connecter</Link>
                            <Link href="/signup" className="text-lg font-medium py-2 text-blue-400">S'inscrire</Link>
                        </>
                    )}
                </motion.div>
            )}
        </nav>
    );
}


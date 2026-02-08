'use client';

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ChevronRight, Shield, Sparkles, Zap } from 'lucide-react';

export default function Hero() {
    return (
        <section className="relative min-h-[90vh] flex items-center pt-20 overflow-hidden">
            {/* Background mesh gradients */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full z-0">
                <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-blue-600/20 rounded-full blur-[120px] animate-pulse" />
                <div className="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] bg-purple-600/10 rounded-full blur-[120px] animate-pulse" style={{ animationDelay: '2s' }} />
            </div>

            <div className="container mx-auto px-6 relative z-10 grid lg:grid-cols-2 gap-16 items-center">
                <motion.div
                    initial={{ opacity: 0, x: -30 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.8 }}
                >
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-bold tracking-widest uppercase mb-6">
                        <Zap size={14} /> Intelligence Augmentée
                    </div>
                    <h1 className="text-5xl md:text-7xl font-extrabold leading-[1.1] mb-6">
                        Négociation <br />
                        <span className="gradient-text">Autonome par IA</span>
                    </h1>
                    <p className="text-xl text-white/50 leading-relaxed mb-10 max-w-xl">
                        Une plateforme d’agents IA capable de négocier de manière autonome une <strong>offre de reprise</strong> et de structurer une <strong>nouvelle offre</strong> (achat, LLD, abonnement) pour chaque client.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-4">
                        <Link
                            href="/signup"
                            className="px-8 py-4 rounded-2xl bg-white text-black font-bold text-lg hover:bg-blue-50 transition-all flex items-center justify-center gap-2 group shadow-xl shadow-white/5"
                        >
                            Démarrer l'Expérience
                            <ChevronRight size={20} className="group-hover:translate-x-1 transition-transform" />
                        </Link>
                        <Link
                            href="#features"
                            className="px-8 py-4 rounded-2xl bg-white/5 border border-white/10 text-white font-bold text-lg hover:bg-white/10 transition-all flex items-center justify-center gap-2"
                        >
                            Découvrir OMEGA
                        </Link>
                    </div>

                    <div className="mt-12 flex items-center gap-6 text-white/30">
                        <div className="flex items-center gap-2">
                            <Shield size={18} />
                            <span className="text-sm font-medium">Sécurité JWT</span>
                        </div>
                        <div className="w-1 h-1 bg-white/10 rounded-full" />
                        <div className="flex items-center gap-2">
                            <Sparkles size={18} />
                            <span className="text-sm font-medium">IA Mistral</span>
                        </div>
                    </div>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, scale: 0.9, rotate: 5 }}
                    animate={{ opacity: 1, scale: 1, rotate: 0 }}
                    transition={{ duration: 1, delay: 0.2 }}
                    className="relative hidden lg:block"
                >
                    <div className="absolute inset-0 bg-blue-600/20 blur-[100px] rounded-full scale-75" />
                    <div className="relative glass border border-white/10 rounded-[2.5rem] p-4 bg-black/40 shadow-2xl overflow-hidden aspect-video flex flex-col">
                        <div className="flex items-center justify-between mb-8 px-4 py-2 border-b border-white/5">
                            <div className="flex gap-2">
                                <div className="w-3 h-3 rounded-full bg-red-500/50" />
                                <div className="w-3 h-3 rounded-full bg-yellow-500/50" />
                                <div className="w-3 h-3 rounded-full bg-green-500/50" />
                            </div>
                            <div className="px-3 py-1 rounded-lg bg-white/5 text-[10px] text-white/40 font-mono tracking-tighter">
                                OMEGA_CORE_v2.0.4
                            </div>
                        </div>
                        <div className="flex-1 space-y-4 px-6 overflow-hidden">
                            <div className="w-[80%] h-4 bg-white/5 rounded-full animate-pulse" />
                            <div className="w-[60%] h-4 bg-white/5 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
                            <div className="w-full h-32 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-3xl border border-white/10 flex items-center justify-center relative overflow-hidden group/analysis">
                                {/* Scanning Line */}
                                <motion.div
                                    className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-blue-400 to-transparent z-10 opacity-50"
                                    animate={{
                                        top: ["0%", "100%", "0%"],
                                    }}
                                    transition={{
                                        duration: 4,
                                        repeat: Infinity,
                                        ease: "linear"
                                    }}
                                />

                                {/* Data Visualization Bars */}
                                <div className="absolute inset-0 flex items-center justify-around px-8 opacity-20">
                                    {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                                        <motion.div
                                            key={i}
                                            className="w-1 bg-blue-400 rounded-full"
                                            animate={{ height: ["20%", "60%", "30%", "80%", "20%"] }}
                                            transition={{
                                                duration: 2.5,
                                                repeat: Infinity,
                                                delay: i * 0.1
                                            }}
                                        />
                                    ))}
                                </div>

                                <motion.div
                                    animate={{ opacity: [0.3, 0.7, 0.3] }}
                                    transition={{ duration: 2, repeat: Infinity }}
                                    className="relative flex flex-col items-center gap-2"
                                >

                                </motion.div>
                            </div>
                        </div>
                    </div>
                </motion.div>
            </div>
        </section>
    );
}


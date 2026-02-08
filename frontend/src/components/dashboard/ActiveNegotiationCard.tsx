'use client';

import { GlassCard } from '@/components/UI/GlassCard';
import { MessageSquare, Clock, ArrowRight, CheckCircle2 } from 'lucide-react';
import Link from 'next/link';
import { motion } from 'framer-motion';

export function ActiveNegotiationCard() {
    // Mock data - in real app would come from API
    const hasActiveNegotiation = true;
    const negotiationStatus = 'OFFER_RECEIVED'; // WAITING_USER, PROCESSING, OFFER_RECEIVED, COMPLETED
    const vehicleName = 'Dacia Sandero Stepway';

    if (!hasActiveNegotiation) {
        return (
            <GlassCard className="h-full flex flex-col justify-center items-center text-center p-8 space-y-4">
                <div className="p-4 rounded-full bg-white/5 mx-auto">
                    <MessageSquare size={32} className="text-gray-400" />
                </div>
                <div>
                    <h3 className="text-xl font-bold text-white">Aucune négociation active</h3>
                    <p className="text-gray-400 text-sm mt-2">Commencez une nouvelle recherche pour trouver votre véhicule idéal.</p>
                </div>
                <Link
                    href="/chat"
                    className="mt-4 px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors"
                >
                    Démarrer
                </Link>
            </GlassCard>
        );
    }

    return (
        <GlassCard className="h-full relative overflow-hidden group">
            <div className="flex justify-between items-start mb-6">
                <div>
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                        Négociation en cours
                    </h3>
                    <p className="text-gray-400 text-sm mt-1">Dernière activité: il y a 2 min</p>
                </div>
                <div className="px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-xs font-medium border border-blue-500/30">
                    Offre reçue
                </div>
            </div>

            <div className="space-y-6">
                <div className="flex items-center gap-4">
                    <div className="w-16 h-16 rounded-lg bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center border border-white/10">
                        <span className="text-2xl">🚗</span>
                    </div>
                    <div>
                        <div className="text-lg font-bold text-white">{vehicleName}</div>
                        <div className="text-sm text-gray-400">Offre OMEGA: 180,000 MAD</div>
                    </div>
                </div>

                <div className="space-y-3">
                    <div className="flex items-center gap-3 text-sm text-gray-300">
                        <CheckCircle2 size={16} className="text-green-500" />
                        <span>Analyse du marché terminée</span>
                    </div>
                    <div className="flex items-center gap-3 text-sm text-gray-300">
                        <CheckCircle2 size={16} className="text-green-500" />
                        <span>Véhicule de reprise évalué</span>
                    </div>
                    <div className="flex items-center gap-3 text-sm text-white font-medium">
                        <Clock size={16} className="text-blue-400" />
                        <span>En attente de votre réponse</span>
                    </div>
                </div>

                <Link
                    href="/chat"
                    className="w-full mt-4 flex items-center justify-center gap-2 py-3 bg-white/10 hover:bg-white/20 rounded-lg text-white font-medium transition-all group-hover:translate-x-1"
                >
                    <span>Reprendre la discussion</span>
                    <ArrowRight size={18} />
                </Link>
            </div>

            {/* Background decoration */}
            <div className="absolute -top-10 -right-10 w-40 h-40 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
        </GlassCard>
    );
}

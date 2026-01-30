/**
 * Dashboard Page
 * --------------
 * Provides a high-level overview of the user's fiscal health, 
 * active negotiations, and personalized market insights.
 */
'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { User, Bell, ChevronRight, TrendingUp, Sparkles, Activity, Target, Zap, BarChart3, Clock, ArrowUpRight } from 'lucide-react';
import Link from 'next/link';
import { UserProfile } from '@/components/dashboard/UserProfile';
import { FiscalHealth } from '@/components/dashboard/FiscalHealth';
import { ActiveNegotiationCard } from '@/components/dashboard/ActiveNegotiationCard';
import { userService } from '@/services/userService';
import { marketService } from '@/services/marketService';
import { GlassCard } from '@/components/UI/GlassCard';
import { PageBackground } from '@/components/UI/PageBackground';
import Navbar from '@/components/Navbar/Navbar';
import Footer from '@/components/Footer/Footer';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { CompleteProfileModal } from '@/components/dashboard/CompleteProfileModal';

export default function DashboardPage() {
    const [userData, setUserData] = useState<Record<string, any> | null>(null);
    const [mounted, setMounted] = useState(false);
    const [marketStats, setMarketStats] = useState<any | null>(null);
    const [marketLoading, setMarketLoading] = useState(false);
    const [showCompleteProfileModal, setShowCompleteProfileModal] = useState(false);

    useEffect(() => {
        setMounted(true);
        const fetchData = async () => {
            try {
                const data = await userService.getUserProfile();
                setUserData(data);
            } catch (error) {
                console.error('Failed to fetch user profile:', error);
            }
        };
        fetchData();
    }, []);

    useEffect(() => {
        if (!userData) return;
        const modelGuess =
            (userData.preferences?.brands && userData.preferences.brands[0] ? `${userData.preferences.brands[0]} ${userData.preferences?.model || ''}` : '')
                .trim();

        let mounted = true;
        const fetchMarket = async () => {
            setMarketLoading(true);
            try {
                const data = await marketService.getMarketTrends(modelGuess);
                if (!mounted) return;
                setMarketStats(data.result);
            } catch (err) {
                console.error('fetchMarket error', err);
            } finally {
                if (mounted) setMarketLoading(false);
            }
        };
        fetchMarket();
        return () => { mounted = false; };
    }, [userData]);

    const containerVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: {
            opacity: 1,
            y: 0,
            transition: { staggerChildren: 0.1, delayChildren: 0.2 }
        }
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 10 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.3 } }
    };

    const getMissingFieldsCount = (data: any) => {
        if (!data) return 6;

        const requiredFields = {
            'Max Budget': data.financials?.max_budget_mad,
            'Type de Paiement': data.financials?.preferred_payment,
            'Limite Mensuelle': data.financials?.monthly_limit_mad,
            'Dettes Actuelles': data.financials?.current_debts_mad,
            'Marques Préférées': data.preferences?.brands?.length > 0,
            'Catégorie': data.preferences?.category,
            'Carburant': data.preferences?.fuel_type,
            'Transmission': data.preferences?.transmission
        };

        const missing = Object.values(requiredFields).filter(val => !val);
        return missing.length;
    };

    if (!mounted) return null;

    const stats = [
        { label: 'Négociations Actives', value: '3', icon: Target, color: 'from-blue-500 to-blue-600', lightColor: 'bg-blue-500/20' },
        { label: 'Score Performance', value: '92%', icon: Zap, color: 'from-purple-500 to-purple-600', lightColor: 'bg-purple-500/20' },
        { label: 'Économies Réalisées', value: '45K DH', icon: TrendingUp, color: 'from-green-500 to-green-600', lightColor: 'bg-green-500/20' }
    ];

    const recentActivities = [
        { id: 1, title: 'Négociation mise à jour', time: '2h', icon: Target },
        { id: 2, title: 'Nouvelle offre reçue', time: '4h', icon: Sparkles },
        { id: 3, title: 'Profil complété', time: '1j', icon: User }
    ];

    const content = (
        <PageBackground className="pb-20 pt-10">
            <Navbar />

            {/* HEADER SECTION - FULL SCREEN WIDTH */}
            <motion.div
                className="w-screen relative left-[calc(-50vw+50%)] px-4 sm:px-6 lg:px-8 mb-12"
                variants={itemVariants}
                initial="hidden"
                animate="visible"
            >
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
                    <div>
                        <h1 className="text-4xl md:text-5xl font-bold text-white mb-2">
                            Bienvenue, <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                                {userData?.full_name?.split(' ')[0] || 'Utilisateur'}
                            </span>
                        </h1>
                        <p className="text-gray-400 text-base md:text-lg">
                            Dashboard OMEGA - Gérez vos négociations et découvrez des opportunités
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <button className="relative p-3 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 transition-all">
                            <Bell size={20} className="text-white" />
                            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                        </button>
                        <Link
                            href="/profile"
                            className="flex items-center gap-2 px-5 py-3 rounded-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-medium transition-all shadow-lg shadow-blue-600/30"
                        >
                            <User size={18} />
                            Mon Profil
                        </Link>
                    </div>
                </div>
            </motion.div>

            {/* STATS CARDS - FULL SCREEN WIDTH */}
            <motion.div className="w-screen relative left-[calc(-50vw+50%)] px-4 sm:px-6 lg:px-8 mb-12" variants={containerVariants} initial="hidden" animate="visible">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                    {stats.map((stat, idx) => {
                        const Icon = stat.icon;
                        return (
                            <motion.div key={idx} variants={itemVariants}>
                                <GlassCard className="p-6 border-white/10 hover:border-white/20 transition-all group overflow-hidden">
                                    <div className="flex items-start justify-between mb-6">
                                        <div className={`p-3 rounded-lg ${stat.lightColor}`}>
                                            <Icon className="text-white" size={24} />
                                        </div>
                                        <div className="flex items-center gap-1 text-green-400 text-sm font-bold">
                                            <ArrowUpRight size={16} />
                                            +12%
                                        </div>
                                    </div>
                                    <p className="text-gray-400 text-sm mb-2">{stat.label}</p>
                                    <h3 className="text-3xl font-bold text-white">{stat.value}</h3>
                                </GlassCard>
                            </motion.div>
                        );
                    })}
                </div>
            </motion.div>

            {/* MAIN GRID - FULL SCREEN WIDTH */}
            <motion.div className="w-screen relative left-[calc(-50vw+50%)] px-4 sm:px-6 lg:px-8 mb-12" variants={containerVariants} initial="hidden" animate="visible">
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">

                    {/* LEFT COLUMN - PROFILE (1 col) */}
                    <motion.div className="lg:col-span-1" variants={itemVariants}>
                        <UserProfile data={userData} />
                    </motion.div>

                    {/* CENTER COLUMN - NEGOTIATIONS & TRENDS (2 cols) */}
                    <motion.div className="lg:col-span-2 space-y-6" variants={containerVariants}>

                        {/* Active Negotiation */}
                        <motion.div variants={itemVariants}>
                            <ActiveNegotiationCard />
                        </motion.div>

                        {/* Market Trends & Offers */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                            {/* MARKET TRENDS CARD */}
                            <motion.div variants={itemVariants}>
                                <GlassCard className="p-6 border-white/10 hover:border-white/20 transition-all group h-full">
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="p-3 rounded-lg bg-orange-500/20">
                                            <BarChart3 className="text-orange-400" size={22} />
                                        </div>
                                        <span className="text-xs font-bold text-green-400 bg-green-500/15 px-2.5 py-1 rounded-full">
                                            +12%
                                        </span>
                                    </div>
                                    <h4 className="text-base font-bold text-white mb-1">Tendances Marché</h4>
                                    <p className="text-sm text-gray-400 mb-4">
                                        {marketStats ? `${marketStats.inventory.avg_market_price?.toLocaleString() || 'N/A'} DH (moy.)` : 'Chargement...'}
                                    </p>
                                    <Link
                                        href="/market"
                                        className="text-orange-400 text-sm font-semibold flex items-center gap-1 hover:gap-2 transition-all hover:text-orange-300"
                                    >
                                        Voir les analyses <ChevronRight size={16} />
                                    </Link>
                                </GlassCard>
                            </motion.div>

                            {/* PREMIUM OFFERS CARD */}
                            <motion.div variants={itemVariants}>
                                <GlassCard className="p-6 border-white/10 hover:border-white/20 transition-all group h-full">
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="p-3 rounded-lg bg-purple-500/20">
                                            <Sparkles className="text-purple-400" size={22} />
                                        </div>
                                        <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${getMissingFieldsCount(userData) === 0
                                            ? 'text-green-400 bg-green-500/15'
                                            : 'text-purple-400 bg-purple-500/15'
                                            }`}>
                                            {getMissingFieldsCount(userData) === 0 ? '✓ Complet' : `${getMissingFieldsCount(userData)} manquants`}
                                        </span>
                                    </div>
                                    <h4 className="text-base font-bold text-white mb-1">Offres Premium</h4>
                                    <p className="text-sm text-gray-400 mb-4">
                                        {getMissingFieldsCount(userData) > 0
                                            ? 'Complétez vos informations pour accéder aux meilleures offres.'
                                            : 'Opportunités sélectionnées pour vous.'
                                        }
                                    </p>

                                    {getMissingFieldsCount(userData) > 0 ? (
                                        <button
                                            onClick={() => setShowCompleteProfileModal(true)}
                                            className="text-purple-400 text-sm font-semibold flex items-center gap-1 hover:gap-2 transition-all hover:text-purple-300 w-full text-left"
                                        >
                                            Compléter le profil <ChevronRight size={16} />
                                        </button>
                                    ) : (
                                        <Link
                                            href="/market"
                                            className="text-purple-400 text-sm font-semibold flex items-center gap-1 hover:gap-2 transition-all hover:text-purple-300"
                                        >
                                            Découvrir les offres <ChevronRight size={16} />
                                        </Link>
                                    )}
                                </GlassCard>
                            </motion.div>
                        </div>
                    </motion.div>

                    {/* MODALS */}
                    <CompleteProfileModal
                        isOpen={showCompleteProfileModal}
                        onClose={() => setShowCompleteProfileModal(false)}
                        userData={userData}
                        onUpdate={(newData) => setUserData(newData)}
                    />

                    {/* RIGHT COLUMN - FISCAL HEALTH (1 col) */}
                    <motion.div className="lg:col-span-1" variants={itemVariants}>
                        <FiscalHealth data={{
                            income: userData?.income_mad,
                            score: 85
                        }} />
                    </motion.div>
                </div>
            </motion.div>

            {/* RECENT ACTIVITY SECTION - FULL SCREEN WIDTH */}
            <motion.div className="w-screen relative left-[calc(-50vw+50%)] px-4 sm:px-6 lg:px-8 mb-12" variants={itemVariants} initial="hidden" animate="visible">
                <GlassCard className="p-8 border-white/10">
                    <div className="flex items-center justify-between mb-8">
                        <div className="flex items-center gap-3">
                            <div className="p-3 rounded-lg bg-blue-500/20">
                                <Activity className="text-blue-400" size={24} />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-white">Activités Récentes</h3>
                                <p className="text-xs text-gray-500 mt-1">Vos dernières actions</p>
                            </div>
                        </div>
                        <Link href="/activity" className="text-blue-400 text-sm font-semibold hover:text-blue-300 transition-colors">
                            Voir tout →
                        </Link>
                    </div>

                    <div className="space-y-3">
                        {recentActivities.map((activity) => {
                            const ActivityIcon = activity.icon;
                            return (
                                <motion.div
                                    className="flex items-center gap-4 p-4 rounded-lg bg-white/5 hover:bg-white/10 transition-all group cursor-pointer border border-transparent hover:border-white/10"
                                    variants={itemVariants}
                                    key={activity.id}
                                >
                                    <div className="flex-shrink-0 p-2.5 rounded-lg bg-blue-500/20 group-hover:bg-blue-500/30 transition-all">
                                        <ActivityIcon size={18} className="text-blue-400" />
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-white font-medium text-sm">{activity.title}</p>
                                        <p className="text-xs text-gray-500 mt-1">il y a {activity.time}</p>
                                    </div>
                                    <ChevronRight size={16} className="text-white/30 group-hover:text-white/60 transition-colors" />
                                </motion.div>
                            );
                        })}
                    </div>
                </GlassCard>
            </motion.div>

            <Footer />
        </PageBackground>
    );

    return <ProtectedRoute>{content}</ProtectedRoute>;
}

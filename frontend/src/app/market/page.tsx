/**
 * Market Page
 * -----------
 * Displays real-time market trends, brand filters, and price evolution charts.
 * Uses Framer Motion for premium animations and Recharts for data visualization.
 */
'use client';

import { useEffect, useState } from 'react';
import { Search, Loader2, TrendingDown, TrendingUp, Info } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { marketService, MarketData } from '@/services/marketService';
import { GlassCard } from '@/components/UI/GlassCard';
import { PageBackground } from '@/components/UI/PageBackground';
import Navbar from '@/components/Navbar/Navbar';
import Footer from '@/components/Footer/Footer';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { motion } from 'framer-motion';

export default function MarketPage() {
    const [mounted, setMounted] = useState(false);
    const [model, setModel] = useState('');
    const [stats, setStats] = useState<MarketData | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [chartData, setChartData] = useState<Array<{ month: string; price: number }>>([]);

    const [brands, setBrands] = useState<string[]>([]);

    useEffect(() => {
        setMounted(true);
        loadBrands();
        // fetchTrends(model); // Don't fetch automatically on empty model
    }, []);

    const loadBrands = async () => {
        const fetchedBrands = await marketService.getBrands();
        if (fetchedBrands && fetchedBrands.length > 0) {
            setBrands(fetchedBrands);
        } else {
            // Fallback brands if API fails or returns empty
            setBrands(['Renault', 'Dacia', 'Peugeot', 'Volkswagen', 'Hyundai', 'Toyota']);
        }
    };

    const fetchTrends = async (targetModel: string) => {
        console.log('[market] fetchTrends start', targetModel);
        setLoading(true);
        setError(null);
        try {
            // Récupérer les données du marché
            const res = await marketService.getMarketTrends(targetModel);
            console.log('[market] API response', res);
            setStats(res.result);

            // Récupérer les données du graphique
            const chart = await marketService.getChartData(targetModel);
            setChartData(chart);
        } catch (err: any) {
            console.error('[market] fetch error', err);
            setError(err?.message || 'Erreur inconnue');
            setStats(null);
            setChartData([]);
        } finally {
            setLoading(false);
        }
    };

    // Fonction pour gérer la recherche
    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (model.trim()) {
            fetchTrends(model); // Utiliser le model actuel
        }
    };

    const containerVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: {
            opacity: 1,
            y: 0,
            transition: {
                staggerChildren: 0.1
            }
        }
    };

    if (!mounted) return null;

    if (loading && !stats) {
        return (
            <PageBackground className="p-0">
                <Navbar />
                <div className="flex-1 flex items-center justify-center pt-28">
                    <Loader2 className="animate-spin text-blue-500" size={48} />
                </div>
                <Footer />
            </PageBackground>
        );
    }

    const content = (
        <PageBackground className="pb-12 pt-10">
            <Navbar />
            <motion.div
                className="container mx-auto px-4"
                variants={containerVariants}
                initial="hidden"
                animate="visible"
            >
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
                    <div>
                        <motion.h1
                            className="text-4xl font-bold text-white mb-2"
                            variants={containerVariants}
                        >
                            Analyses du Marché
                        </motion.h1>
                        <p className="text-blue-200/60">Intelligence prédictive et tendances de prix en temps réel.</p>
                    </div>

                    <form onSubmit={handleSearch} className="relative w-full md:w-96">
                        <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                            <Search className="w-5 h-5 text-white/30" />
                        </div>
                        <input
                            type="text"
                            value={model}
                            onChange={(e) => setModel(e.target.value)}
                            placeholder="Rechercher un modèle..."
                            className="w-full bg-white/5 border border-white/10 rounded-2xl pl-12 pr-4 py-3.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-all shadow-xl"
                        />
                        <button
                            type="submit"
                            disabled={loading}
                            className="absolute right-4 top-1/2 -translate-y-1/2 text-blue-400 hover:text-blue-300 disabled:opacity-50 cursor-pointer"
                        >
                            {loading ? <Loader2 className="animate-spin w-5 h-5" /> : <Search className="w-5 h-5" />}
                        </button>
                    </form>
                </div>

                {/* Brand Filter Pills */}
                <motion.div
                    variants={containerVariants}
                    className="flex flex-wrap gap-2 mb-10"
                >
                    {brands.map((brand) => (
                        <button
                            key={brand}
                            onClick={() => {
                                setModel(brand);
                                fetchTrends(brand);
                            }}
                            className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${model.toLowerCase().includes(brand.toLowerCase())
                                ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/25'
                                : 'bg-white/5 text-white/60 hover:bg-white/10 hover:text-white border border-white/5 hover:border-white/10'
                                }`}
                        >
                            {brand}
                        </button>
                    ))}
                    <button
                        onClick={() => {
                            setModel('');
                            setStats(null);
                        }}
                        className="px-4 py-2 rounded-full text-sm font-medium bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/20 transition-all"
                    >
                        Réinitialiser
                    </button>
                </motion.div>

                {stats && chartData.length > 0 ? (
                    <div className="space-y-8">
                        {/* Stats Overview */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                            <GlassCard className="p-6">
                                <p className="text-sm text-white/50 mb-1 font-medium italic">Prix Moyen</p>
                                <h3 className="text-2xl font-bold text-white">
                                    {stats.inventory.avg_market_price.toLocaleString('fr-MA')} DH
                                </h3>
                            </GlassCard>
                            <GlassCard className="p-6">
                                <p className="text-sm text-white/50 mb-1 font-medium italic">Prix Min / Max</p>
                                <div className="flex items-end gap-2 text-white">
                                    <h3 className="text-2xl font-bold">
                                        {stats.inventory.min_price.toLocaleString('fr-MA')} DH
                                    </h3>
                                    <span className="text-xs text-white/30 mb-1.5">
                                        - {stats.inventory.max_price.toLocaleString('fr-MA')} DH
                                    </span>
                                </div>
                            </GlassCard>
                            <GlassCard className="p-6">
                                <p className="text-sm text-white/50 mb-1 font-medium italic">Kilométrage Moyen</p>
                                <h3 className="text-2xl font-bold text-white">
                                    {Math.round(stats.inventory.avg_mileage).toLocaleString('fr-MA')} km
                                </h3>
                            </GlassCard>
                            <GlassCard className="p-6">
                                <p className="text-sm text-white/50 mb-1 font-medium italic">Tendance</p>
                                <div className="flex items-center gap-2">
                                    {stats.market_trends.trend_direction === 'down' ? (
                                        <div className="flex items-center gap-2 text-green-400">
                                            <TrendingDown className="w-6 h-6" />
                                            <span className="text-2xl font-bold">Baisse</span>
                                        </div>
                                    ) : (
                                        <div className="flex items-center gap-2 text-orange-400">
                                            <TrendingUp className="w-6 h-6" />
                                            <span className="text-2xl font-bold">Hausse</span>
                                        </div>
                                    )}
                                </div>
                            </GlassCard>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                            {/* Main Chart */}
                            <GlassCard className="lg:col-span-2 p-8 h-[500px] flex flex-col">
                                <div className="flex justify-between items-start mb-8">
                                    <div>
                                        <h3 className="text-xl font-bold text-white mb-1">Évolution des Prix</h3>
                                        <p className="text-sm text-white/40">Projection sur les 6 derniers mois</p>
                                    </div>
                                </div>
                                <div className="flex-1 w-full h-[400px] min-h-[400px]">
                                    {chartData && chartData.length > 0 ? (
                                        <ResponsiveContainer width="100%" height="100%">
                                            <AreaChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 30 }}>
                                                <defs>
                                                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                                    </linearGradient>
                                                </defs>
                                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                                                <XAxis
                                                    dataKey="month"
                                                    axisLine={false}
                                                    tickLine={false}
                                                    tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 12 }}
                                                />
                                                <YAxis
                                                    axisLine={false}
                                                    tickLine={false}
                                                    tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 12 }}
                                                    tickFormatter={(val) => `${(val / 1000).toFixed(0)}k`}
                                                    width={50}
                                                    domain={['auto', 'auto']}
                                                />
                                                <Tooltip
                                                    contentStyle={{
                                                        backgroundColor: 'rgba(15, 15, 15, 0.95)',
                                                        border: '1px solid rgba(255,255,255,0.1)',
                                                        borderRadius: '12px',
                                                        color: '#fff'
                                                    }}
                                                    itemStyle={{ color: '#fff' }}
                                                    formatter={(val: any) => `${val?.toLocaleString('fr-MA')} DH`}
                                                />
                                                <Area
                                                    type="monotone"
                                                    dataKey="price"
                                                    stroke="#3b82f6"
                                                    strokeWidth={3}
                                                    fillOpacity={1}
                                                    fill="url(#colorPrice)"
                                                    animationDuration={1500}
                                                />
                                            </AreaChart>
                                        </ResponsiveContainer>
                                    ) : (
                                        <div className="flex items-center justify-center h-full text-white/40">
                                            Chargement du graphique...
                                        </div>
                                    )}
                                </div>
                            </GlassCard>

                            {/* Sidebar Insights */}
                            <div className="space-y-6">
                                <GlassCard className="p-6">
                                    <div className="flex items-center gap-3 mb-4">
                                        <div className="p-2 bg-blue-500/20 rounded-lg">
                                            <Info className="w-5 h-5 text-blue-400" />
                                        </div>
                                        <h4 className="font-bold text-white">Insight OMEGA</h4>
                                    </div>
                                    <p className="text-blue-100/70 text-sm leading-relaxed mb-6">
                                        {`Score de demande: ${stats.market_trends.demand_score}/100 - Niveau: ${stats.market_trends.demand_level}`}
                                    </p>
                                    <div className="p-4 bg-white/5 rounded-xl border border-white/5">
                                        <p className="text-xs text-white/40 mb-2 uppercase font-bold tracking-wider italic">Score de confiance</p>
                                        <div className="flex items-center gap-4">
                                            <div className="flex-1 bg-white/10 h-2 rounded-full overflow-hidden">
                                                <div className="bg-blue-500 h-full rounded-full w-[92%]" />
                                            </div>
                                            <span className="text-white font-bold">92%</span>
                                        </div>
                                    </div>
                                </GlassCard>

                                <GlassCard className="p-6 border-white/10">
                                    <h4 className="font-bold text-white mb-4">Volume d'Annonces</h4>
                                    <div className="flex items-center justify-between">
                                        <span className="text-white/50 text-sm">Disponibilité :</span>
                                        <span className={`px-3 py-1 rounded-full text-xs font-bold ${stats.inventory.stock_available > 50
                                            ? 'bg-green-500/20 text-green-400'
                                            : 'bg-orange-500/20 text-orange-400'
                                            }`}>
                                            {stats.inventory.stock_available} véhicules
                                        </span>
                                    </div>
                                </GlassCard>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center py-20 text-center">
                        <div className="w-20 h-20 bg-blue-500/10 rounded-full flex items-center justify-center mb-6 border border-blue-500/20">
                            {
                                loading ? (
                                    <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
                                ) : (
                                    <Search className="w-10 h-10 text-blue-500/40" />
                                )}
                        </div>
                        <h3 className="text-xl font-bold text-white mb-2">
                            {loading ? 'Analyse du marché en cours...' : error ? 'Aucune donnée trouvée' : 'Rechercher une Analyse'}
                        </h3>
                        <p className="text-white/40 max-w-sm mb-6">
                            {loading
                                ? 'Nous récupérons les dernières tendances pour ce modèle.'
                                : error
                                    ? `Impossible de trouver des données pour "${model}". Essayez une marque populaire ci-dessus.`
                                    : 'Sélectionnez une marque ou entrez un modèle pour voir les statistiques.'
                            }
                        </p>
                    </div>
                )
                }

                {
                    error && (
                        <div className="mt-8 p-4 bg-red-500/20 border border-red-500/30 rounded-xl">
                            <p className="text-red-400 text-center">Erreur: {error}</p>
                        </div>
                    )
                }
            </motion.div >
            <Footer />
        </PageBackground >
    );

    return (
        <ProtectedRoute>
            {content}
        </ProtectedRoute>
    );
}


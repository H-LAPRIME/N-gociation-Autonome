'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { User as UserIcon, Shield, MapPin, Car, Edit2, ChevronLeft, Wallet } from 'lucide-react';
import { userService } from '@/services/userService';
import { GlassCard } from '@/components/UI/GlassCard';
import { PageBackground } from '@/components/UI/PageBackground';
import Navbar from '@/components/Navbar/Navbar';
import Footer from '@/components/Footer/Footer';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

export default function ProfilePage() {
    const { updateUser } = useAuth();
    const [user, setUser] = useState<Record<string, any> | null>(null);
    const [loading, setLoading] = useState(true);
    const [mounted, setMounted] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [formData, setFormData] = useState<Record<string, any>>({
        full_name: '',
        city: '',
        income_mad: 0,
        financials: { max_budget_mad: 0 },
        preferences: { brands: [], category: '' }
    });
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        setMounted(true);
        const loadProfile = async () => {
            try {
                const data = await userService.getUserProfile();
                setUser(data);
                setFormData({
                    full_name: data.full_name || '',
                    city: data.city || '',
                    income_mad: data.income_mad || 0,
                    financials: {
                        max_budget_mad: data.financials?.max_budget_mad || 0
                    },
                    preferences: {
                        brands: data.preferences?.brands || [],
                        category: data.preferences?.category || ''
                    }
                });
            } catch (err) {
                console.error("Failed to load profile", err);
            } finally {
                setLoading(false);
            }
        };
        loadProfile();
    }, []);

    const handleSave = async () => {
        setSaving(true);
        try {
            await userService.updateUserProfile(formData);
            const updatedProfile = { ...user, ...formData };
            setUser(updatedProfile);
            updateUser({
                full_name: formData.full_name,
                city: formData.city,
                income_mad: formData.income_mad
            });
            setIsEditing(false);
        } catch (err) {
            alert("Erreur lors de la mise à jour");
        } finally {
            setSaving(false);
        }
    };

    if (!mounted) return null;

    if (loading) {
        return (
            <PageBackground className="p-0">
                <Navbar />
                <div className="flex-1 flex items-center justify-center pt-28">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
                </div>
                <Footer />
            </PageBackground>
        );
    }

    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                staggerChildren: 0.1
            }
        }
    };

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
                            className="text-3xl md:text-4xl font-bold text-white mb-2"
                            variants={containerVariants}
                        >
                            Mon Profil
                        </motion.h1>
                        <p className="text-blue-200/60">Gérez vos informations personnelles et vos préférences automobiles.</p>
                    </div>
                    <Link
                        href="/dashboard"
                        className="inline-flex items-center gap-2 text-white/70 hover:text-white transition-colors bg-white/5 hover:bg-white/10 px-4 py-2 rounded-full border border-white/10"
                    >
                        <ChevronLeft className="w-4 h-4" />
                        Retour au Dashboard
                    </Link>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Sidebar - Profile Card */}
                    <div className="lg:col-span-1 space-y-6">
                        <GlassCard className="p-8 text-center">
                            <div className="relative w-32 h-32 mx-auto mb-6">
                                <div className="absolute inset-0 bg-blue-500/20 rounded-full blur-xl animate-pulse"></div>
                                <div className="relative w-full h-full rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center border-2 border-white/20 shadow-xl">
                                    <UserIcon className="w-16 h-16 text-white" />
                                </div>
                                <button className="absolute bottom-0 right-0 p-2 bg-blue-500 rounded-full text-white shadow-lg hover:bg-blue-600 transition-colors border border-white/20">
                                    <Edit2 className="w-4 h-4" />
                                </button>
                            </div>
                            <h2 className="text-2xl font-bold text-white mb-1">{user?.full_name}</h2>
                            <p className="text-blue-200/60 flex items-center justify-center gap-1 mb-6">
                                <MapPin className="w-4 h-4" />
                                {user?.city || 'Non spécifié'}
                            </p>
                            <div className="flex flex-col gap-3">
                                <button
                                    onClick={() => setIsEditing(!isEditing)}
                                    className={`w-full py-3 rounded-xl font-medium transition-all ${isEditing
                                        ? 'bg-white/10 text-white hover:bg-white/20'
                                        : 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg shadow-blue-600/20'
                                        }`}
                                >
                                    {isEditing ? 'Annuler' : 'Modifier le Profil'}
                                </button>
                            </div>
                        </GlassCard>

                        {/* Quick Stats/Info */}
                        <GlassCard className="p-6 space-y-4">
                            <h3 className="text-sm font-semibold text-white/40 uppercase tracking-wider">Récapitulatif</h3>
                            <div className="flex items-center gap-4 p-3 rounded-lg bg-white/5 border border-white/5">
                                <div className="p-2 bg-green-500/20 rounded-lg">
                                    <Wallet className="w-5 h-5 text-green-400" />
                                </div>
                                <div>
                                    <p className="text-xs text-white/50">Budget Maximum</p>
                                    <p className="font-semibold text-white">{user?.financials?.max_budget_mad?.toLocaleString()} DH</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-4 p-3 rounded-lg bg-white/5 border border-white/5">
                                <div className="p-2 bg-blue-500/20 rounded-lg">
                                    <Car className="w-5 h-5 text-blue-400" />
                                </div>
                                <div>
                                    <p className="text-xs text-white/50">Préférence Catégorie</p>
                                    <p className="font-semibold text-white">{user?.preferences?.category || 'Non spécifié'}</p>
                                </div>
                            </div>
                        </GlassCard>
                    </div>

                    {/* Main Content Area */}
                    <div className="lg:col-span-2 space-y-8">
                        {/* Form / Display Section */}
                        <GlassCard className="p-8">
                            <div className="flex items-center gap-3 mb-8 pb-4 border-b border-white/10">
                                <Shield className="w-6 h-6 text-blue-400" />
                                <h3 className="text-xl font-semibold text-white">Informations Personnelles</h3>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <label className="text-sm text-white/60 ml-1">Nom Complet</label>
                                    {isEditing ? (
                                        <input
                                            type="text"
                                            value={formData.full_name}
                                            onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                                            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-all"
                                        />
                                    ) : (
                                        <div className="bg-white/5 border border-transparent rounded-xl px-4 py-3 text-white">
                                            {user?.full_name}
                                        </div>
                                    )}
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm text-white/60 ml-1">Ville</label>
                                    {isEditing ? (
                                        <input
                                            type="text"
                                            value={formData.city}
                                            onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                                            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-all"
                                        />
                                    ) : (
                                        <div className="bg-white/5 border border-transparent rounded-xl px-4 py-3 text-white">
                                            {user?.city}
                                        </div>
                                    )}
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm text-white/60 ml-1">Revenu Mensuel (DH)</label>
                                    {isEditing ? (
                                        <input
                                            type="number"
                                            value={formData.income_mad}
                                            onChange={(e) => setFormData({ ...formData, income_mad: Number(e.target.value) })}
                                            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-all"
                                        />
                                    ) : (
                                        <div className="bg-white/5 border border-transparent rounded-xl px-4 py-3 text-white">
                                            {user?.income_mad?.toLocaleString()} DH
                                        </div>
                                    )}
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm text-white/60 ml-1">Budget Max (DH)</label>
                                    {isEditing ? (
                                        <input
                                            type="number"
                                            value={formData.financials.max_budget_mad}
                                            onChange={(e) => setFormData({
                                                ...formData,
                                                financials: { ...formData.financials, max_budget_mad: Number(e.target.value) }
                                            })}
                                            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-all"
                                        />
                                    ) : (
                                        <div className="bg-white/5 border border-transparent rounded-xl px-4 py-3 text-white">
                                            {user?.financials?.max_budget_mad?.toLocaleString()} DH
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Preferences Section */}
                            <div className="mt-12">
                                <div className="flex items-center gap-3 mb-8 pb-4 border-b border-white/10">
                                    <Car className="w-6 h-6 text-blue-400" />
                                    <h3 className="text-xl font-semibold text-white">Préférences Automobiles</h3>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="space-y-2">
                                        <label className="text-sm text-white/60 ml-1">Marques Favoris</label>
                                        <div className="flex flex-wrap gap-2">
                                            {user?.preferences?.brands?.map((brand: string, i: number) => (
                                                <span key={i} className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-sm border border-blue-500/30">
                                                    {brand}
                                                </span>
                                            )) || <span className="text-white/40 italic text-sm">Aucune marque</span>}
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-sm text-white/60 ml-1">Catégorie</label>
                                        <div className="bg-white/5 border border-transparent rounded-xl px-4 py-3 text-white">
                                            {user?.preferences?.category || 'Non spécifié'}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {isEditing && (
                                <div className="mt-12 flex justify-end gap-4">
                                    <button
                                        onClick={() => setIsEditing(false)}
                                        className="px-6 py-2 rounded-xl text-white/60 hover:text-white transition-colors"
                                    >
                                        Annuler
                                    </button>
                                    <button
                                        onClick={handleSave}
                                        disabled={saving}
                                        className="px-8 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium shadow-lg shadow-blue-600/20 transition-all disabled:opacity-50"
                                    >
                                        {saving ? 'Enregistrement...' : 'Enregistrer les modifications'}
                                    </button>
                                </div>
                            )}
                        </GlassCard>
                    </div>
                </div>
            </motion.div>
            <Footer />
        </PageBackground>
    );

    return (
        <ProtectedRoute>
            {content}
        </ProtectedRoute>
    );
}


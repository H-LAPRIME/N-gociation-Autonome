'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, ChevronLeft, Check, User, Mail, Lock, MapPin, Wallet, Briefcase, Car, Shield, Loader2 } from 'lucide-react';
import { GlassCard } from '@/components/UI/GlassCard';

export default function SignupPage() {
    const [step, setStep] = useState(1);
    const [formData, setFormData] = useState({
        full_name: '',
        email: '',
        password: '',
        city: '',
        income_mad: '',
        max_budget_mad: '',
        brand_preference: '',
        contract_type: 'CDI',
        current_debts_mad: '',
        usage: 'Mixte'
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [mounted, setMounted] = useState(false);
    const { signup } = useAuth();
    const router = useRouter();

    useEffect(() => {
        setMounted(true);
    }, []);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const nextStep = () => setStep(step + 1);
    const prevStep = () => setStep(step - 1);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            // Build a clean payload matching UserCreate schema
            const payload = {
                email: formData.email,
                password: formData.password,
                full_name: formData.full_name,
                city: formData.city,
                income_mad: parseFloat(formData.income_mad) || 0,
                financials: {
                    max_budget_mad: parseFloat(formData.max_budget_mad) || 0,
                    contract_type: formData.contract_type,
                    current_debts_mad: parseFloat(formData.current_debts_mad) || 0
                },
                preferences: {
                    brands: formData.brand_preference ? [formData.brand_preference] : [],
                    usage: formData.usage
                }
            };

            await signup(payload);
            router.push('/chat');
        } catch (err) {
            setError((err as any).message || 'Une erreur est survenue lors de l&apos;inscription.');
        } finally {
            setLoading(false);
        }
    };

    const stepVariants = {
        enter: { opacity: 0, x: 20 },
        center: { opacity: 1, x: 0 },
        exit: { opacity: 0, x: -20 }
    };

    if (!mounted) return null;

    return (
        <div className="min-h-screen flex items-center justify-center p-6 relative overflow-hidden bg-[#020205]">
            {/* Background decorative elements */}
            <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px] -mr-64 -mt-64" />
            <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-purple-600/10 rounded-full blur-[120px] -ml-64 -mb-64" />

            <div className="max-w-xl w-full">
                <div className="text-center mb-8">
                    <h1 className="text-4xl font-bold mb-2">Rejoignez OMEGA</h1>
                    <p className="text-white/40">L&apos;expertise automobile augmentée par l&apos;IA</p>
                </div>

                {/* Stepper Progress */}
                <div className="flex justify-between items-center mb-10 px-4 relative">
                    <div className="absolute left-4 right-4 h-[2px] bg-white/5 top-1/2 -translate-y-1/2 z-0" />
                    {[1, 2, 3].map((s) => (
                        <div
                            key={s}
                            className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold z-10 transition-all duration-500 ${step >= s
                                ? 'bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-lg shadow-blue-500/20'
                                : 'bg-white/5 text-white/40 border border-white/10'
                                }`}
                        >
                            {step > s ? <Check size={18} strokeWidth={3} /> : s}
                        </div>
                    ))}
                </div>

                <GlassCard className="p-8 md:p-10" glow={step === 3}>
                    {error && (
                        <div className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit}>
                        <AnimatePresence mode="wait">
                            {step === 1 && (
                                <motion.div
                                    key="step1"
                                    variants={stepVariants}
                                    initial="enter"
                                    animate="center"
                                    exit="exit"
                                    className="space-y-6"
                                >
                                    <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
                                        <User className="text-blue-400" size={20} /> Compte Personnel
                                    </h3>
                                    <div className="space-y-4">
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium text-white/60 ml-1">Nom Complet</label>
                                            <div className="relative">
                                                <input name="full_name" value={formData.full_name} onChange={handleChange} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-blue-500 focus:bg-white/10 transition-all" required placeholder="Ex: Mohammed Alami" />
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium text-white/60 ml-1">Email</label>
                                            <div className="relative">
                                                <Mail className="absolute right-4 top-1/2 -translate-y-1/2 text-white/20" size={18} />
                                                <input name="email" type="email" value={formData.email} onChange={handleChange} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-blue-500 focus:bg-white/10 transition-all" required placeholder="nom@exemple.com" />
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium text-white/60 ml-1">Mot de passe</label>
                                            <div className="relative">
                                                <Lock className="absolute right-4 top-1/2 -translate-y-1/2 text-white/20" size={18} />
                                                <input name="password" type="password" value={formData.password} onChange={handleChange} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-blue-500 focus:bg-white/10 transition-all" required placeholder="••••••••" />
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            )}

                            {step === 2 && (
                                <motion.div key="step2" variants={stepVariants} initial="enter" animate="center" exit="exit" className="space-y-6">
                                    <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
                                        <Briefcase className="text-purple-400" size={20} /> Profil Financier
                                    </h3>
                                    <div className="space-y-4">
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium text-white/60 ml-1">Ville</label>
                                            <div className="relative">
                                                <MapPin className="absolute right-4 top-1/2 -translate-y-1/2 text-white/20" size={18} />
                                                <input name="city" value={formData.city} onChange={handleChange} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-purple-500 focus:bg-white/10 transition-all" placeholder="Ex: Casablanca" />
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-2">
                                                <label className="text-sm font-medium text-white/60 ml-1">Revenu (MAD)</label>
                                                <input name="income_mad" type="number" value={formData.income_mad} onChange={handleChange} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-purple-500" placeholder="10000" />
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-sm font-medium text-white/60 ml-1">Dettes (MAD)</label>
                                                <input name="current_debts_mad" type="number" value={formData.current_debts_mad} onChange={handleChange} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-purple-500" placeholder="0" />
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium text-white/60 ml-1">Type de Contrat</label>
                                            <select name="contract_type" value={formData.contract_type} onChange={handleChange} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-purple-500 appearance-none text-white">
                                                <option value="CDI" className="bg-[#020205]">CDI</option>
                                                <option value="CDD" className="bg-[#020205]">CDD</option>
                                                <option value="Fonctionnaire" className="bg-[#020205]">Fonctionnaire</option>
                                                <option value="Libéral" className="bg-[#020205]">Libéral</option>
                                                <option value="Privé" className="bg-[#020205]">Auto-Entrepreneur</option>
                                            </select>
                                        </div>
                                    </div>
                                </motion.div>
                            )}

                            {step === 3 && (
                                <motion.div key="step3" variants={stepVariants} initial="enter" animate="center" exit="exit" className="space-y-6">
                                    <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
                                        <Shield className="text-cyan-400" size={20} /> Préférences Véhicule
                                    </h3>
                                    <div className="space-y-4">
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium text-white/60 ml-1">Budget Maximal (MAD)</label>
                                            <div className="relative">
                                                <Wallet className="absolute right-4 top-1/2 -translate-y-1/2 text-white/20" size={18} />
                                                <input name="max_budget_mad" type="number" value={formData.max_budget_mad} onChange={handleChange} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-cyan-500" placeholder="200000" />
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium text-white/60 ml-1">Marque Favorite</label>
                                            <div className="relative">
                                                <Car className="absolute right-4 top-1/2 -translate-y-1/2 text-white/20" size={18} />
                                                <input name="brand_preference" value={formData.brand_preference} onChange={handleChange} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-cyan-500" placeholder="Ex: Peugeot, Audi..." />
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium text-white/60 ml-1">Usage Principal</label>
                                            <select name="usage" value={formData.usage} onChange={handleChange} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-cyan-500 appearance-none text-white">
                                                <option value="Trajet travail" className="bg-[#020205]">Trajet travail</option>
                                                <option value="Famille" className="bg-[#020205]">Famille</option>
                                                <option value="Loisirs" className="bg-[#020205]">Loisirs / Route</option>
                                                <option value="Mixte" className="bg-[#020205]">Mixte</option>
                                            </select>
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        <div className="flex gap-4 mt-10">
                            {step > 1 && (
                                <button
                                    type="button"
                                    onClick={prevStep}
                                    className="px-6 py-4 rounded-xl border border-white/10 hover:bg-white/5 font-semibold flex items-center gap-2 transition-all"
                                >
                                    <ChevronLeft size={20} /> Précédent
                                </button>
                            )}

                            {step < 3 ? (
                                <button
                                    type="button"
                                    onClick={nextStep}
                                    className="flex-1 py-4 bg-white/10 hover:bg-white/15 text-white font-semibold rounded-xl border border-white/10 flex items-center justify-center gap-2 transition-all group"
                                >
                                    Suivant <ChevronRight size={20} className="group-hover:translate-x-1 transition-transform" />
                                </button>
                            ) : (
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="flex-1 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold rounded-xl shadow-lg shadow-blue-600/20 flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
                                >
                                    {loading ? <Loader2 className="animate-spin" size={20} /> : (
                                        <>Lancer l'expérience <Check size={20} /></>
                                    )}
                                </button>
                            )}
                        </div>
                    </form>

                    <div className="mt-8 text-center text-sm text-white/40">
                        Déjà inscrit&nbsp;?{' '}
                        <Link href="/login" className="text-blue-400 hover:text-blue-300 font-medium transition-colors">
                            Se connecter
                        </Link>
                    </div>
                </GlassCard>
            </div>
        </div>
    );
}


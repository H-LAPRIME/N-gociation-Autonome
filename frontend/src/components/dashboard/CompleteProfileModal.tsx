import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Save, AlertCircle, CheckCircle2 } from 'lucide-react';
import { GlassCard } from '@/components/UI/GlassCard';
import { userService } from '@/services/userService';

interface CompleteProfileModalProps {
    isOpen: boolean;
    onClose: () => void;
    userData: any;
    onUpdate: (newData: any) => void;
}

export const CompleteProfileModal = ({ isOpen, onClose, userData, onUpdate }: CompleteProfileModalProps) => {
    const [loading, setLoading] = useState(false);

    // Add useEffect to sync state with props when userData changes

    useEffect(() => {
        if (userData) {
            setFormData({
                city: userData.city || '',
                income_mad: userData.income_mad || '',
                contract_type: userData.financials?.contract_type || 'CDI',
                max_budget_mad: userData.financials?.max_budget_mad || '',
                category: userData.preferences?.category || 'SUV',
                fuel_type: userData.preferences?.fuel_type || 'Diesel',
                transmission: userData.preferences?.transmission || 'Automatique'
            });
        }
    }, [userData]);

    // Identify missing fields
    const isMissingCity = !userData?.city;
    const isMissingIncome = !userData?.income_mad;
    const isMissingContract = !userData?.financials?.contract_type;
    const isMissingBudget = !userData?.financials?.max_budget_mad;
    const isMissingCategory = !userData?.preferences?.category;
    const isMissingFuel = !userData?.preferences?.fuel_type;
    const isMissingTransmission = !userData?.preferences?.transmission;

    const [formData, setFormData] = useState({
        city: userData?.city || '',
        income_mad: userData?.income_mad || '',
        contract_type: userData?.financials?.contract_type || 'CDI',
        max_budget_mad: userData?.financials?.max_budget_mad || '',
        category: userData?.preferences?.category || 'SUV',
        fuel_type: userData?.preferences?.fuel_type || 'Diesel',
        transmission: userData?.preferences?.transmission || 'Automatique'
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const updates: any = {};

            if (isMissingCity) updates.city = formData.city;
            if (isMissingIncome) updates.income_mad = Number(formData.income_mad);

            if (isMissingContract || isMissingBudget) {
                updates.financials = {
                    ...userData.financials,
                    ...(isMissingContract && { contract_type: formData.contract_type }),
                    ...(isMissingBudget && { max_budget_mad: Number(formData.max_budget_mad) })
                };
            }

            if (isMissingCategory || isMissingFuel || isMissingTransmission) {
                updates.preferences = {
                    ...userData.preferences,
                    ...(isMissingCategory && { category: formData.category }),
                    ...(isMissingFuel && { fuel_type: formData.fuel_type }),
                    ...(isMissingTransmission && { transmission: formData.transmission })
                };
            }

            await userService.updateUserProfile(updates);

            // Construct full new user object to update parent state locally
            const newUserData = {
                ...userData,
                ...updates,
                financials: {
                    ...userData.financials,
                    ...(updates.financials || {})
                },
                preferences: {
                    ...userData.preferences,
                    ...(updates.preferences || {})
                }
            };

            onUpdate(newUserData);
            onClose();
        } catch (error) {
            console.error('Failed to update profile:', error);
            alert("Erreur lors de la mise à jour.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                    />

                    {/* Modal Content */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="relative w-full max-w-lg"
                    >
                        <GlassCard className="p-0 overflow-hidden border-white/20 shadow-2xl shadow-blue-900/20">
                            {/* Header */}
                            <div className="relative p-6 bg-gradient-to-r from-blue-600/20 to-purple-600/20 border-b border-white/10">
                                <button
                                    onClick={onClose}
                                    className="absolute top-4 right-4 p-2 text-white/50 hover:text-white hover:bg-white/10 rounded-full transition-colors"
                                >
                                    <X size={20} />
                                </button>
                                <div className="flex items-center gap-3">
                                    <div className="p-3 bg-blue-500/20 rounded-xl border border-blue-500/30">
                                        <CheckCircle2 className="w-6 h-6 text-blue-400" />
                                    </div>
                                    <div>
                                        <h2 className="text-xl font-bold text-white">Complétez votre profil</h2>
                                        <p className="text-sm text-blue-200/70">
                                            Remplissez ces informations pour obtenir des offres précises.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* Form */}
                            <form onSubmit={handleSubmit} className="p-6 space-y-5">
                                {isMissingCity && (
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-gray-300 ml-1">📍 Ville de résidence</label>
                                        <input
                                            type="text"
                                            required
                                            value={formData.city}
                                            onChange={(e) => setFormData(prev => ({ ...prev, city: e.target.value }))}
                                            placeholder="Ex: Casablanca, Rabat..."
                                            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
                                        />
                                    </div>
                                )}

                                {isMissingContract && (
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-gray-300 ml-1">📄 Type de Contrat</label>
                                        <select
                                            value={formData.contract_type}
                                            onChange={(e) => setFormData(prev => ({ ...prev, contract_type: e.target.value }))}
                                            className="w-full bg-[#020205] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all appearance-none cursor-pointer"
                                        >
                                            <option value="CDI">CDI</option>
                                            <option value="CDD">CDD</option>
                                            <option value="Fonctionnaire">Fonctionnaire</option>
                                            <option value="Libéral">Profession Libérale</option>
                                            <option value="Retraité">Retraité</option>
                                        </select>
                                    </div>
                                )}

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                                    {isMissingIncome && (
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium text-gray-300 ml-1">💰 Revenu Mensuel (DH)</label>
                                            <input
                                                type="number"
                                                required
                                                min="0"
                                                value={formData.income_mad}
                                                onChange={(e) => setFormData(prev => ({ ...prev, income_mad: e.target.value }))}
                                                placeholder="0.00"
                                                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
                                            />
                                        </div>
                                    )}

                                    {isMissingBudget && (
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium text-gray-300 ml-1">🏷️ Budget Max (DH)</label>
                                            <input
                                                type="number"
                                                min="0"
                                                value={formData.max_budget_mad}
                                                onChange={(e) => setFormData(prev => ({ ...prev, max_budget_mad: e.target.value }))}
                                                placeholder="0.00"
                                                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
                                            />
                                        </div>
                                    )}
                                </div>

                                {/* Vehicle Preferences */}
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    {isMissingCategory && (
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium text-gray-300 ml-1">🚙 Catégorie</label>
                                            <select
                                                value={formData.category}
                                                onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value }))}
                                                className="w-full bg-[#020205] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all appearance-none cursor-pointer"
                                            >
                                                <option value="SUV">SUV</option>
                                                <option value="Berline">Berline</option>
                                                <option value="Citadine">Citadine</option>
                                                <option value="Coupé">Coupé</option>
                                                <option value="Pick-up">Pick-up</option>
                                            </select>
                                        </div>
                                    )}
                                    {isMissingFuel && (
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium text-gray-300 ml-1">⛽ Carburant</label>
                                            <select
                                                value={formData.fuel_type}
                                                onChange={(e) => setFormData(prev => ({ ...prev, fuel_type: e.target.value }))}
                                                className="w-full bg-[#020205] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all appearance-none cursor-pointer"
                                            >
                                                <option value="Diesel">Diesel</option>
                                                <option value="Essence">Essence</option>
                                                <option value="Hybride">Hybride</option>
                                                <option value="Électrique">Électrique</option>
                                            </select>
                                        </div>
                                    )}
                                    {isMissingTransmission && (
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium text-gray-300 ml-1">⚙️ Boîte</label>
                                            <select
                                                value={formData.transmission}
                                                onChange={(e) => setFormData(prev => ({ ...prev, transmission: e.target.value }))}
                                                className="w-full bg-[#020205] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all appearance-none cursor-pointer"
                                            >
                                                <option value="Automatique">Auto</option>
                                                <option value="Manuelle">Manuelle</option>
                                            </select>
                                        </div>
                                    )}
                                </div>

                                {!isMissingCity && !isMissingIncome && !isMissingContract && !isMissingBudget && !isMissingCategory && !isMissingFuel && !isMissingTransmission && (
                                    <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/20 flex items-center gap-3 text-green-400">
                                        <CheckCircle2 size={24} />
                                        <div className="text-sm font-medium">Votre profil est déjà complet !</div>
                                    </div>
                                )}

                                <div className="pt-2">
                                    <button
                                        type="submit"
                                        disabled={loading || (!isMissingCity && !isMissingIncome && !isMissingContract && !isMissingBudget && !isMissingCategory && !isMissingFuel && !isMissingTransmission)}
                                        className="w-full py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold rounded-xl shadow-lg shadow-blue-600/20 border border-white/10 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                    >
                                        {loading ? (
                                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                        ) : (
                                            <>
                                                <Save size={18} />
                                                Enregistrer le profil
                                            </>
                                        )}
                                    </button>
                                </div>
                            </form>
                        </GlassCard>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
};

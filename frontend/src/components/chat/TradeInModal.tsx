'use client';

import { X } from 'lucide-react';
import { useState } from 'react';

interface TradeInModalProps {
    isOpen: boolean;
    onClose: () => void;
    initialData?: any;
    onSubmit?: (data: TradeInData) => void;
}

interface TradeInData {
    brand: string;
    model: string;
    year: number;
    mileage: number;
    condition: string;
}

export function TradeInModal({ isOpen, onClose, initialData, onSubmit }: TradeInModalProps) {
    const [formData, setFormData] = useState<TradeInData>({
        brand: initialData?.brand || '',
        model: initialData?.model || '',
        year: initialData?.year || new Date().getFullYear(),
        mileage: initialData?.mileage || 0,
        condition: initialData?.condition || 'Bon',
    });

    const [errors, setErrors] = useState<Partial<Record<keyof TradeInData, string>>>({});

    if (!isOpen) return null;

    const handleChange = (field: keyof TradeInData, value: string | number) => {
        setFormData(prev => ({ ...prev, [field]: value }));
        // Clear error when user starts typing
        if (errors[field]) {
            setErrors(prev => ({ ...prev, [field]: undefined }));
        }
    };

    const validateForm = (): boolean => {
        const newErrors: Partial<Record<keyof TradeInData, string>> = {};

        if (!formData.brand.trim()) newErrors.brand = 'La marque est requise';
        if (!formData.model.trim()) newErrors.model = 'Le modèle est requis';
        if (!formData.year || formData.year < 1900 || formData.year > new Date().getFullYear() + 1) {
            newErrors.year = 'Année invalide';
        }
        if (!formData.mileage || formData.mileage < 0) {
            newErrors.mileage = 'Kilométrage invalide';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = () => {
        if (!validateForm()) return;

        // Call the onSubmit callback if provided
        if (onSubmit) {
            onSubmit(formData);
        }

        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-lg rounded-2xl border border-white/10 bg-[#141416] p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
                <div className="mb-6 flex items-center justify-between">
                    <h2 className="text-xl font-bold text-white">Détails de Reprise</h2>
                    <button onClick={onClose} className="rounded-full p-1 hover:bg-white/10 text-white">
                        <X size={20} />
                    </button>
                </div>

                <div className="space-y-4">
                    <p className="text-sm text-gray-400">
                        Veuillez compléter les informations pour votre estimation.
                    </p>

                    {/* Form fields */}
                    <div className="grid gap-4">
                        {/* Brand */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-300">Marque *</label>
                            <input
                                type="text"
                                value={formData.brand}
                                onChange={(e) => handleChange('brand', e.target.value)}
                                className={`w-full rounded-lg border ${errors.brand ? 'border-red-500' : 'border-white/10'} bg-white/5 p-3 text-white focus:border-blue-500 focus:outline-none`}
                                placeholder="Ex: Dacia, Peugeot, Renault..."
                            />
                            {errors.brand && <p className="text-xs text-red-400">{errors.brand}</p>}
                        </div>

                        {/* Model */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-300">Modèle *</label>
                            <input
                                type="text"
                                value={formData.model}
                                onChange={(e) => handleChange('model', e.target.value)}
                                className={`w-full rounded-lg border ${errors.model ? 'border-red-500' : 'border-white/10'} bg-white/5 p-3 text-white focus:border-blue-500 focus:outline-none`}
                                placeholder="Ex: Sandero, 208, Clio..."
                            />
                            {errors.model && <p className="text-xs text-red-400">{errors.model}</p>}
                        </div>

                        {/* Year */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-300">Année *</label>
                            <input
                                type="number"
                                value={formData.year}
                                onChange={(e) => handleChange('year', parseInt(e.target.value) || 0)}
                                className={`w-full rounded-lg border ${errors.year ? 'border-red-500' : 'border-white/10'} bg-white/5 p-3 text-white focus:border-blue-500 focus:outline-none`}
                                placeholder="Ex: 2020"
                                min="1900"
                                max={new Date().getFullYear() + 1}
                            />
                            {errors.year && <p className="text-xs text-red-400">{errors.year}</p>}
                        </div>

                        {/* Mileage */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-300">Kilométrage (km) *</label>
                            <input
                                type="number"
                                value={formData.mileage}
                                onChange={(e) => handleChange('mileage', parseInt(e.target.value) || 0)}
                                className={`w-full rounded-lg border ${errors.mileage ? 'border-red-500' : 'border-white/10'} bg-white/5 p-3 text-white focus:border-blue-500 focus:outline-none`}
                                placeholder="Ex: 45000"
                                min="0"
                            />
                            {errors.mileage && <p className="text-xs text-red-400">{errors.mileage}</p>}
                        </div>

                        {/* Condition */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-300">État général</label>
                            <select
                                value={formData.condition}
                                onChange={(e) => handleChange('condition', e.target.value)}
                                className="w-full rounded-lg border border-white/10 bg-white/5 p-3 text-white focus:border-blue-500 focus:outline-none"
                            >
                                <option value="Excellent" className="bg-[#121214]">Excellent</option>
                                <option value="Très bon" className="bg-[#121214]">Très bon</option>
                                <option value="Bon" className="bg-[#121214]">Bon</option>
                                <option value="Moyen" className="bg-[#121214]">Moyen</option>
                                <option value="À rénover" className="bg-[#121214]">À rénover</option>
                            </select>
                        </div>
                    </div>

                    <div className="mt-6 flex justify-end gap-3">
                        <button
                            onClick={onClose}
                            className="rounded-lg px-4 py-2 text-sm font-medium text-gray-400 hover:text-white transition-colors"
                        >
                            Annuler
                        </button>
                        <button
                            onClick={handleSubmit}
                            className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-500 transition-colors"
                        >
                            Estimer ma voiture
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

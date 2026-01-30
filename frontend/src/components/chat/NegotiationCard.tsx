import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, X, RefreshCw, Clock, Wallet, ChevronDown, ChevronUp, History, Trash, AlertTriangle, CheckCircle, XCircle, Info } from 'lucide-react';
import { GlassCard } from '@/components/UI/GlassCard';
import { negotiationService, NegotiationHistory, NegotiationMessageRequest } from '@/services/negotiationService';

interface ValidationInfo {
    is_approved: boolean;
    audit_trail: string[];
    violations: string[];
    confidence_score: number;
}

interface NegotiationCardProps {
    sessionId: string;
    initialOffer: Record<string, any>;
    maxRounds: number;
    currentRound: number;
    onNegotiationUpdate: (data: any) => void;
    onReset?: () => void;
}

export const NegotiationCard: React.FC<NegotiationCardProps> = ({
    sessionId,
    initialOffer,
    maxRounds,
    currentRound: initialRound,
    onNegotiationUpdate,
    onReset
}) => {
    const [currentOffer, setCurrentOffer] = useState<Record<string, any>>(initialOffer);
    const [round, setRound] = useState(initialRound);
    const [status, setStatus] = useState('active');
    const [isLoading, setIsLoading] = useState(false);
    const [showCounterForm, setShowCounterForm] = useState(false);
    const [showHistory, setShowHistory] = useState(false);
    const [history, setHistory] = useState<NegotiationHistory[]>([]);
    const [validationInfo, setValidationInfo] = useState<ValidationInfo | null>(null);
    const [showValidation, setShowValidation] = useState(false);

    // Counter offer inputs
    const [counterPrice, setCounterPrice] = useState(initialOffer.offer_price_mad || 0);

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('fr-MA', { style: 'currency', currency: 'MAD' }).format(amount);
    };

    const fetchHistory = async () => {
        try {
            const data = await negotiationService.getHistory(sessionId);
            setHistory(data);
        } catch (error) {
            console.error("Failed to fetch history", error);
        }
    };

    useEffect(() => {
        if (showHistory) {
            fetchHistory();
        }
    }, [showHistory, sessionId]);

    const handleAction = async (action: 'accept' | 'reject' | 'counter', message?: string) => {
        setIsLoading(true);
        try {
            const payload: NegotiationMessageRequest = {
                action: action,
                message: message || (action === 'accept' ? "J'accepte cette offre." : "Je refuse cette offre.")
            };

            if (action === 'counter') {
                payload.counter_offer = {
                    desired_price: Number(counterPrice)
                };
                payload.message = `Je propose ${counterPrice} MAD.`;
            }

            const response = await negotiationService.sendMessage(sessionId, payload);

            // Update local state
            setRound(response.round);
            if (response.revised_offer) {
                setCurrentOffer(response.revised_offer);
            }
            setStatus(response.status);
            setShowCounterForm(false);

            // Handle validation info from response
            if (response.validation_info) {
                setValidationInfo(response.validation_info);
                setShowValidation(true);
                // Auto-hide after 10 seconds
                setTimeout(() => setShowValidation(false), 12500);
            }

            // Notify parent to show agent message in chat
            onNegotiationUpdate({
                role: 'assistant',
                content: response.agent_response,
                timestamp: Date.now()
            });

        } catch (error) {
            console.error("Negotiation action failed", error);
        } finally {
            setIsLoading(false);
        }
    };

    if (!currentOffer) return null;

    const isCompleted = status === 'completed';
    const isRejected = status === 'rejected';
    const isMaxRounds = status === 'max_rounds_reached';

    return (
        <div className="w-full max-w-lg mx-auto my-2">
            <GlassCard className="!bg-black/80 border-blue-500/30 overflow-hidden relative !backdrop-blur-none transition-all duration-500">
                {/* Header */}
                <div className="p-3 border-b border-white/10 flex justify-between items-center bg-blue-600/10">
                    <div className="flex items-center gap-2">
                        <Wallet className="text-blue-400" size={16} />
                        <span className="font-bold text-sm text-white">Négociation en cours</span>
                    </div>
                    <div className="flex items-center gap-2">
                        {onReset && (
                            <button
                                onClick={onReset}
                                className="p-1 rounded-full hover:bg-white/10 text-white/50 hover:text-red-400 transition-colors"
                                title="Réinitialiser la négociation"
                            >
                                <Trash size={12} />
                            </button>
                        )}
                        <Clock size={12} className="text-white/50" />
                        <span className="text-[10px] font-mono text-white/70">
                            Tour {round}/{maxRounds}
                        </span>
                    </div>
                </div>

                {/* Validation Notifications */}
                <AnimatePresence>
                    {showValidation && validationInfo && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden"
                        >
                            <div className={`p-3 border-b flex flex-col gap-2 ${validationInfo.is_approved
                                ? 'bg-green-500/10 border-green-500/20'
                                : 'bg-red-500/10 border-red-500/20'
                                }`}>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        {validationInfo.is_approved ? (
                                            <CheckCircle className="text-green-400" size={16} />
                                        ) : (
                                            <XCircle className="text-red-400" size={16} />
                                        )}
                                        <span className={`text-xs font-bold ${validationInfo.is_approved ? 'text-green-400' : 'text-red-400'
                                            }`}>
                                            {validationInfo.is_approved ? 'Validation Business Réussie' : 'Violation Business Détectée'}
                                        </span>
                                    </div>
                                    <button
                                        onClick={() => setShowValidation(false)}
                                        className="text-white/30 hover:text-white/60 transition-colors"
                                    >
                                        <X size={14} />
                                    </button>
                                </div>

                                <div className="max-h-[300px] overflow-y-auto pr-2 custom-scrollbar space-y-3">
                                    <div className="text-[11px] text-white/70 italic leading-tight px-1 space-y-1">
                                        {validationInfo.is_approved ? (
                                            <p>Votre offre a été validée avec succès par notre système de contrôle de gestion.</p>
                                        ) : (
                                            <div>
                                                <p className="text-red-300 font-bold mb-1">Offre non conforme :</p>
                                                <ul className="list-disc list-inside space-y-0.5">
                                                    {validationInfo.violations.map((v, i) => (
                                                        <li key={i} className="text-red-200/80 not-italic">{v}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}

                                        {validationInfo.audit_trail.some(log => log.includes('⚠️')) && (
                                            <div className="mt-2 pt-2 border-t border-white/5">
                                                <p className="text-yellow-300/80 font-bold mb-1 flex items-center gap-1">
                                                    <AlertTriangle size={10} /> Attention (Points de vigilance) :
                                                </p>
                                                <ul className="list-disc list-inside space-y-0.5 text-yellow-100/60 not-italic">
                                                    {validationInfo.audit_trail
                                                        .filter(log => log.includes('⚠️'))
                                                        .map((warn, i) => (
                                                            <li key={i}>{warn.replace(/^[⚠️][\s]*/, '')}</li>
                                                        ))
                                                    }
                                                </ul>
                                            </div>
                                        )}
                                    </div>

                                    <div className="space-y-1.5">
                                        {validationInfo.audit_trail.map((log, idx) => {
                                            const isPass = log.includes('✅');
                                            const isFail = log.includes('❌');
                                            const isWarn = log.includes('⚠️');
                                            const isInfo = log.includes('ℹ️');

                                            return (
                                                <div key={idx} className="flex items-start gap-2 text-[10px]">
                                                    <div className="mt-0.5">
                                                        {isPass && <CheckCircle className="text-green-400" size={10} />}
                                                        {isFail && <XCircle className="text-red-400" size={10} />}
                                                        {isWarn && <AlertTriangle className="text-yellow-400" size={10} />}
                                                        {isInfo && <Info className="text-blue-400" size={10} />}
                                                        {!isPass && !isFail && !isWarn && !isInfo && <div className="w-2.5 h-2.5 rounded-full bg-white/20" />}
                                                    </div>
                                                    <span className={`${isPass ? 'text-green-300/70' :
                                                        isFail ? 'text-red-300/70' :
                                                            isWarn ? 'text-yellow-300/70' :
                                                                'text-white/50'
                                                        }`}>
                                                        {log.replace(/^[✅❌⚠️ℹ️][\s]*/, '')}
                                                    </span>
                                                </div>
                                            );
                                        })}
                                    </div>

                                    {validationInfo.violations.length > 0 && !validationInfo.is_approved && (
                                        <div className="mt-1 p-2 rounded bg-red-500/20 border border-red-500/30">
                                            <p className="text-[10px] font-bold text-red-200 mb-1 flex items-center gap-1">
                                                <AlertTriangle size={10} /> Détails des Violations:
                                            </p>
                                            <ul className="list-disc list-inside space-y-0.5">
                                                {validationInfo.violations.map((v, i) => (
                                                    <li key={i} className="text-[9px] text-red-100/80">{v}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Offer Details */}
                <div className="p-4 text-center">
                    <p className="text-[11px] text-white/40 mb-0.5 uppercase tracking-widest font-bold">Offre actuelle</p>
                    <motion.div
                        key={currentOffer.offer_price_mad}
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="text-4xl font-black bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent mb-1"
                    >
                        {formatCurrency(currentOffer.offer_price_mad)}
                    </motion.div>

                    {currentOffer.monthly_payment_mad && (
                        <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-[10px] text-blue-400 font-bold uppercase tracking-wider">
                            <span>{formatCurrency(currentOffer.monthly_payment_mad)} / mois</span>
                        </div>
                    )}
                </div>

                {/* Status Banners */}
                {isCompleted && (
                    <div className="bg-green-500/20 border-y border-green-500/30 p-3 text-center">
                        <p className="text-green-400 font-bold flex items-center justify-center gap-2">
                            <Check size={18} /> Offre Acceptée
                        </p>
                        <a
                            href={`${(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api').replace('/api', '')}${currentOffer.pdf_reference || currentOffer.pdf_url}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-white/70 underline mt-1 block hover:text-white transition-colors"
                        >
                            Télécharger le contrat (PDF)
                        </a>
                    </div>
                )}

                {isRejected && (
                    <div className="bg-red-500/20 border-y border-red-500/30 p-3 text-center">
                        <p className="text-red-400 font-bold flex items-center justify-center gap-2">
                            <X size={18} /> Offre Rejetée
                        </p>
                    </div>
                )}

                {/* Actions */}
                {!isCompleted && !isRejected && (
                    <div className="p-3 space-y-2">
                        {!showCounterForm ? (
                            <div className="grid grid-cols-2 gap-2">
                                <button
                                    onClick={() => handleAction('accept')}
                                    disabled={isLoading}
                                    className="col-span-2 bg-green-600 hover:bg-green-500 text-white font-bold py-2.5 rounded-xl transition-all shadow-lg hover:shadow-green-500/20 flex items-center justify-center gap-2 text-sm"
                                >
                                    {isLoading ? <div className="animate-spin w-4 h-4 border-2 border-white/30 border-t-white rounded-full" /> : <Check size={16} />}
                                    Accepter l'offre
                                </button>

                                <button
                                    onClick={() => setShowCounterForm(true)}
                                    disabled={isLoading || isMaxRounds}
                                    className="bg-white/10 hover:bg-white/20 text-white font-bold py-2 rounded-xl transition-all border border-white/10 hover:border-white/20 disabled:opacity-50 flex items-center justify-center gap-2 text-xs"
                                >
                                    <RefreshCw size={14} />
                                    Contre-offre
                                </button>

                                <button
                                    onClick={() => handleAction('reject')}
                                    disabled={isLoading}
                                    className="bg-red-500/10 hover:bg-red-500/20 text-red-400 font-bold py-2 rounded-xl transition-all border border-red-500/20 hover:border-red-500/30 flex items-center justify-center gap-2 text-xs"
                                >
                                    <X size={14} />
                                    Refuser
                                </button>
                            </div>
                        ) : (
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="bg-white/5 rounded-xl p-3 border border-white/10"
                            >
                                <div className="flex justify-between items-center mb-2">
                                    <h4 className="font-bold text-white text-[12px]">Votre proposition</h4>
                                    <button onClick={() => setShowCounterForm(false)} className="text-white/50 hover:text-white">
                                        <X size={14} />
                                    </button>
                                </div>

                                <label className="block text-[10px] text-white/50 mb-1 uppercase tracking-wider font-bold">Prix proposé (MAD)</label>
                                <input
                                    type="number"
                                    value={counterPrice}
                                    onChange={(e) => setCounterPrice(Number(e.target.value))}
                                    className="w-full bg-black/60 border border-white/10 rounded-lg px-3 py-1.5 text-white text-sm outline-none focus:border-blue-500 mb-2"
                                />

                                <button
                                    onClick={() => handleAction('counter')}
                                    disabled={isLoading}
                                    className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 rounded-lg transition-all shadow-lg hover:shadow-blue-500/20 text-xs"
                                >
                                    Envoyer la contre-offre
                                </button>
                            </motion.div>
                        )}
                    </div>
                )}

                {/* History Toggle */}
                <div className="border-t border-white/10">
                    <button
                        onClick={() => setShowHistory(!showHistory)}
                        className="w-full py-1.5 flex items-center justify-center gap-2 text-[10px] text-white/40 hover:text-white/70 hover:bg-white/5 transition-colors"
                    >
                        <History size={10} />
                        {showHistory ? "Masquer l'historique" : "Voir l'historique"}
                        {showHistory ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                    </button>
                </div>

                {/* History View */}
                <AnimatePresence>
                    {showHistory && (
                        <motion.div
                            initial={{ height: 0 }}
                            animate={{ height: 'auto' }}
                            exit={{ height: 0 }}
                            className="bg-black/20 overflow-hidden"
                        >
                            <div className="p-4 space-y-3 max-h-48 overflow-y-auto custom-scrollbar">
                                {history.length === 0 ? (
                                    <p className="text-center text-xs text-white/30 italic">Chargement...</p>
                                ) : (
                                    history.map((h, idx) => (
                                        <div key={idx} className={`flex flex-col gap-1 text-xs ${h.speaker === 'agent' ? 'items-start' : 'items-end'}`}>
                                            <span className="text-white/30 uppercase text-[10px]">{h.speaker === 'agent' ? 'OMEGA' : 'VOUS'} - Tour {h.round_number}</span>
                                            <div className={`p-2 rounded-lg max-w-[90%] ${h.speaker === 'agent'
                                                ? 'bg-blue-500/10 border border-blue-500/20 text-blue-100'
                                                : 'bg-white/10 border border-white/10 text-white/80'
                                                }`}>
                                                {h.message}
                                            </div>
                                            {h.offer_data && (
                                                <span className="text-white/40 font-mono text-[10px]">
                                                    Offre: {formatCurrency(h.offer_data.offer_price_mad || h.offer_data.desired_price)}
                                                </span>
                                            )}
                                        </div>
                                    ))
                                )}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </GlassCard>
        </div>
    );
};

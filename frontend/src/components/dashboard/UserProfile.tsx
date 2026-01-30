import { GlassCard } from '@/components/UI/GlassCard';
import { User, MapPin, CreditCard, Shield } from 'lucide-react';

interface UserProfileProps {
    data: any;
}

export function UserProfile({ data }: UserProfileProps) {
    if (!data) return (
        <GlassCard className="p-8 flex items-center justify-center animate-pulse">
            <div className="text-gray-500 font-medium">Chargement du profil...</div>
        </GlassCard>
    );

    return (
        <GlassCard className="p-6 h-full border-blue-500/10 hover:border-blue-500/30 transition-all group">
            <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-2xl font-bold text-white shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform">
                    {data.full_name ? data.full_name.charAt(0) : 'U'}
                </div>
                <div>
                    <h3 className="font-bold text-white text-lg leading-tight">{data.full_name || 'Utilisateur'}</h3>
                    <p className="text-sm text-gray-400 font-medium">{data.email}</p>
                </div>
            </div>

            <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5">
                    <div className="flex items-center gap-2 text-gray-400">
                        <MapPin size={16} className="text-blue-400" />
                        <span className="text-xs font-semibold uppercase tracking-wider">Ville</span>
                    </div>
                    <span className="text-sm font-bold text-white">{data.city || 'Maroc'}</span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5">
                    <div className="flex items-center gap-2 text-gray-400">
                        <CreditCard size={16} className="text-purple-400" />
                        <span className="text-xs font-semibold uppercase tracking-wider">Budget</span>
                    </div>
                    <span className="text-sm font-bold text-white">
                        {data.financials?.max_budget_mad ? `${data.financials.max_budget_mad.toLocaleString()} MAD` : '-'}
                    </span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5">
                    <div className="flex items-center gap-2 text-gray-400">
                        <Shield size={16} className="text-green-400" />
                        <span className="text-xs font-semibold uppercase tracking-wider">Statut</span>
                    </div>
                    <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 border border-green-500/20">
                        Client Vérifié
                    </span>
                </div>
            </div>
        </GlassCard>
    );
}

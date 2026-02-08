'use client';

import styles from '@/app/dashboard/dashboard.module.css';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { GlassCard } from '@/components/UI/GlassCard';
import { motion } from 'framer-motion';

export interface FiscalHealthProps {
    data?: {
        income?: number;
        expenses?: number;
        savings?: number;
        score?: number;
    };
}

export function FiscalHealth({ data }: FiscalHealthProps) {
    const income = data?.income || 12000;
    const expenses = data?.expenses || 8000;
    const savings = data?.savings || 4000;

    // Calculate percentages
    const savingsRate = Math.round((savings / income) * 100);
    const expensesRate = Math.round((expenses / income) * 100);

    const chartData = [
        { name: 'Épargne', value: savings, color: '#3b82f6' },  // Blue
        { name: 'Dépenses', value: expenses, color: '#ef4444' }, // Red
        { name: 'Disponible', value: income - expenses - savings, color: '#10b981' }, // Green
    ];

    return (
        <GlassCard className="h-full flex flex-col">
            <div className="flex justify-between items-start mb-6">
                <div>
                    <h3 className="text-xl font-bold text-white">Santé Fiscale</h3>
                    <p className="text-sm text-gray-400">Analyse mensuelle</p>
                </div>
                <div className={`px-3 py-1 rounded-full text-xs font-medium border ${(data?.score || 85) >= 80
                    ? 'bg-green-500/20 text-green-300 border-green-500/30'
                    : 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30'
                    }`}>
                    Score: {data?.score || 85}/100
                </div>
            </div>

            <div className="flex-1 flex items-center justify-center relative">
                <div className="h-[220px] w-full relative z-10">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={chartData}
                                innerRadius={65}
                                outerRadius={85}
                                paddingAngle={5}
                                dataKey="value"
                                stroke="none"
                            >
                                {chartData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                                    border: '1px solid rgba(255,255,255,0.1)',
                                    borderRadius: '12px',
                                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                                    color: '#fff'
                                }}
                                itemStyle={{ color: '#fff' }}
                                formatter={(value: number | undefined) => `${(value || 0).toLocaleString()} MAD`}
                            />
                        </PieChart>
                    </ResponsiveContainer>
                    {/* Center Text */}
                    <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                        <span className="text-3xl font-bold text-white">{savingsRate}%</span>
                        <span className="text-xs text-gray-400">Épargne</span>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mt-6">
                <div className="p-3 rounded-lg bg-white/5 border border-white/5">
                    <div className="flex items-center gap-2 mb-1">
                        <div className="w-2 h-2 rounded-full bg-blue-500" />
                        <span className="text-xs text-gray-400">Épargne</span>
                    </div>
                    <div className="text-lg font-bold text-white">{savings.toLocaleString()} MAD</div>
                </div>
                <div className="p-3 rounded-lg bg-white/5 border border-white/5">
                    <div className="flex items-center gap-2 mb-1">
                        <div className="w-2 h-2 rounded-full bg-red-500" />
                        <span className="text-xs text-gray-400">Dépenses</span>
                    </div>
                    <div className="text-lg font-bold text-white">{expenses.toLocaleString()} MAD</div>
                </div>
            </div>
        </GlassCard>
    );
}

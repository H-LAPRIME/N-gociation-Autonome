'use client';

import React from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';

interface GlassCardProps {
    children: React.ReactNode;
    className?: string;
    hover?: boolean;
    glow?: boolean;
    delay?: number;
}

export const GlassCard = ({ children, className, hover = true, glow = false, delay = 0 }: GlassCardProps) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay, ease: [0.4, 0, 0.2, 1] }}
            className={clsx(
                'glass-card relative overflow-hidden',
                hover && 'hover:translate-y-[-4px] hover:border-white/20 hover:bg-white/5 transition-all duration-300',
                glow && 'after:absolute after:inset-0 after:rounded-[inherit] after:shadow-[0_0_20px_rgba(59,130,246,0.1)] after:pointer-events-none',
                className
            )}
        >
            <div className="relative z-10">{children}</div>

            {/* Subtle inner light effect */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent pointer-events-none" />
        </motion.div>
    );
};

'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface PageBackgroundProps {
    children: React.ReactNode;
    className?: string;
}

export function PageBackground({ children, className = "" }: PageBackgroundProps) {
    return (
        <div className={`relative min-h-screen flex flex-col overflow-x-hidden ${className}`}>
            {/* Background mesh gradients - Matching Hero style vibrancy (Darker version) */}
            <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
                <div className="absolute top-[-10%] left-[-10%] w-[800px] h-[800px] bg-blue-600/15 rounded-full blur-[120px] animate-pulse" />
                <div className="absolute bottom-[10%] right-[-5%] w-[900px] h-[900px] bg-purple-600/05 rounded-full blur-[130px] animate-pulse" style={{ animationDelay: '3s' }} />
            </div>

            {/* Main Content Layer */}
            <div className="relative z-10 flex flex-col flex-1 pt-32">
                {children}
            </div>
        </div>
    );
}

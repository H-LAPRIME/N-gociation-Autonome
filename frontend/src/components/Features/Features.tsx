'use client';

import React from 'react';
import styles from './Features.module.css';

const FEATURES = [
    {
        title: 'Analyse de Marché',
        description: "Analyse en temps réel des données du marché de l'occasion pour garantir une valorisation précise.",
    },
    {
        title: 'IA Personnalisée',
        description: 'Capacité à traiter les préférences clients, les stocks disponibles et les objectifs commerciaux.',
    },
    {
        title: 'Offres sur Mesure',
        description: 'Structuration intelligente de nouvelles offres : achat direct, LLD ou abonnements flexibles.',
    },
    {
        title: 'Accord Gagnant-Gagnant',
        description: 'Négociation autonome aboutissant à une proposition optimale et finalisation virtuelle.',
    }
];

export default function Features() {
    return (
        <section id="features" className={styles.features}>
            <div className={`${styles.container} container`}>
                <div className={styles.header}>
                    <h2 className={styles.sectionTitle}>Conçu pour l&apos;<span className="gradient-text">Excellence</span></h2>
                    <p className={styles.sectionSubtitle}>Des fonctionnalités puissantes au service de la nouvelle génération de négociation.</p>
                </div>
                <div className={styles.grid}>
                    {FEATURES.map((feature, index) => (
                        <div key={index} className="glass-card">

                            <h3 className={styles.cardTitle}>{feature.title}</h3>
                            <p className={styles.cardDescription}>{feature.description}</p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}

'use client';

import React from 'react';
import styles from './Stats.module.css';

const STATS = [
    { label: 'Offres Négociées', value: '1.2M+' },
    { label: 'Taux de Succès', value: '98%' },
    { label: 'Heures Gagnées', value: '250k' },
    { label: 'Valeur Générée', value: '2.4B DH' }
];

export default function Stats() {
    return (
        <section className={styles.stats}>
            <div className={`${styles.container} container`}>
                <div className={`${styles.bar} glass`}>
                    {STATS.map((stat, index) => (
                        <div key={index} className={styles.statItem}>
                            <div className={styles.value}>{stat.value}</div>
                            <div className={styles.label}>{stat.label}</div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}

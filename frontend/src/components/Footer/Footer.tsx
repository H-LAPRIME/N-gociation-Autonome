'use client';

import React from 'react';
import Link from 'next/link';
import styles from './Footer.module.css';

export default function Footer() {
    return (
        <footer className={styles.footer}>
            <div className={`${styles.container} container`}>
                <div className={styles.top}>
                    <div className={styles.brand}>
                        <Link href="/" className={styles.logo}>
                            <span className="gradient-text">OMEGA</span>
                        </Link>
                        <p className={styles.description}>
                            L'intelligence agentique au service de vos négociations automobiles.
                        </p>
                    </div>
                    <div className={styles.linkGroup}>
                        <h4 className={styles.header}>Plateforme</h4>
                        <Link href="#features">Fonctionnalités</Link>
                        <Link href="/login">Connexion</Link>
                        <Link href="/signup">Inscription</Link>
                    </div>
                    <div className={styles.linkGroup}>
                        <h4 className={styles.header}>Ressources</h4>
                        <Link href="#">Documentation</Link>
                        <Link href="#">API</Link>
                        <Link href="#">Confidentialité</Link>
                    </div>
                </div>
                <div className={styles.bottom}>
                    <p className={styles.copyright}>
                        © {new Date().getFullYear()} OMEGA Intelligence. Tous droits réservés.
                    </p>
                    <div className={styles.socials}>
                        {/* Icons can be added here */}
                    </div>
                </div>
            </div>
        </footer>
    );
}

import React from 'react';
import { motion } from 'framer-motion';
import { FiArrowLeft, FiCreditCard } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';

import { SubscriptionPanel } from '../components/billing/SubscriptionPanel';
import { ParticleBackground } from '../components/common/ParticleBackground';
import { CyberGrid } from '../components/common/CyberGrid';
import { Scanline } from '../components/common/Scanline';

export const BillingPage: React.FC = () => {
    const navigate = useNavigate();
    return (
        <div className="relative min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 py-8 px-4 overflow-x-hidden">
            <ParticleBackground />
            <CyberGrid animated speed={0.3} />
            <Scanline color="#06b6d4" intensity={0.3} />

            <motion.header
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="relative z-10 max-w-5xl mx-auto mb-8"
            >
                <button
                    onClick={() => navigate(-1)}
                    className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all text-sm text-gray-300 hover:text-white font-mono group mb-6"
                >
                    <FiArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
                    Back
                </button>

                <div className="flex items-center gap-4">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-cyan-400 to-purple-600 flex items-center justify-center shadow-xl shadow-purple-500/25">
                        <FiCreditCard className="w-7 h-7 text-white" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-1">
                            Billing & Subscription
                        </h1>
                        <p className="text-sm text-gray-500 font-mono">
                            Manage your plan, usage, and payment methods
                        </p>
                    </div>
                </div>
            </motion.header>

            <motion.main
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="relative z-10 max-w-5xl mx-auto"
            >
                <SubscriptionPanel />
            </motion.main>
        </div>
    );
};

export default BillingPage;
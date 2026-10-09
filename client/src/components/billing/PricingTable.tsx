import React from 'react';
import { motion } from 'framer-motion';
import { FiZap } from 'react-icons/fi';
import { Link } from 'react-router-dom';

import { TierCard } from './TierCard';
import { useBilling } from '../../hooks/useBilling';

interface PricingTableProps {
    showHeader?: boolean;
    showBillingToggle?: boolean;
}
export const PricingTable: React.FC<PricingTableProps> = ({ showHeader = true, showBillingToggle = true }) => {
    const {
        tiers,
        subscription,
        billingCycle,
        setBillingCycle,
        subscribe,
        isSubscribing,
    } = useBilling();

    return (
        <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            {showHeader && (
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    className="text-center mb-12"
                >
                    <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-cyan-500/10 border border-cyan-500/20 rounded-full mb-4">
                        <FiZap className="w-3 h-3 text-cyan-400" />
                        <span className="text-[10px] text-cyan-400 font-mono uppercase tracking-wider">
                            Pricing
                        </span>
                    </div>

                    <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black mb-4">
                        <span className="text-white">Simple, </span>
                        <span className="shimmer-text">Transparent Pricing</span>
                    </h2>

                    <p className="max-w-2xl mx-auto text-gray-400 text-base sm:text-lg">
                        Choose the perfect plan for your needs. No hidden fees. Cancel anytime.
                    </p>
                </motion.div>
            )}

            {showBillingToggle && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.5 }}
                    className="flex justify-center mb-10"
                >
                    <div className="inline-flex items-center gap-1 p-1 bg-white/5 rounded-full border border-white/10">
                        {(['monthly', 'yearly'] as const).map((cycle) => (
                            <button
                                key={cycle}
                                onClick={() => setBillingCycle(cycle)}
                                className={`px-5 py-2 rounded-full text-xs font-mono uppercase tracking-wider transition-all ${billingCycle === cycle
                                    ? 'bg-gradient-to-r from-cyan-500 to-purple-500 text-white shadow-lg'
                                    : 'text-gray-400 hover:text-white'
                                    }`}
                            >
                                {cycle}
                                {cycle === 'yearly' && (
                                    <span className="ml-2 px-1.5 py-0.5 bg-green-500/20 text-green-400 rounded text-[9px]">
                                        -20%
                                    </span>
                                )}
                            </button>
                        ))}
                    </div>
                </motion.div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {tiers.map((tier,) => (
                    <TierCard
                        key={tier.id}
                        tier={tier}
                        billingCycle={billingCycle}
                        currentTier={subscription?.tier}
                        isPopular={tier.id === 'pro'}
                        onSelect={(tierId) => subscribe(tierId, billingCycle)}
                        isProcessing={isSubscribing}
                    />
                ))}
            </div>

            <motion.p
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: 0.3 }}
                className="text-center text-xs text-gray-500 font-mono mt-10"
            >
                All plans include SSL encryption, GDPR compliance, and 99.9% uptime.
                <br />
                <Link to="/help" className="text-cyan-400 hover:text-cyan-300">
                    Questions? Check our FAQ →
                </Link>
            </motion.p>
        </div>
    );
};

export default PricingTable;

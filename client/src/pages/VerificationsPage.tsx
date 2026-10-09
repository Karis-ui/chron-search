import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
    FiArrowLeft,
    FiAward,
    FiZap,
    FiCheck,
    FiStar,
    FiShield,
    FiTrendingUp,
} from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';

import { GradientButton } from '../components/billing/../common/GradientButton';
import { GlassCard } from '../components/common/GlassCard';
import { NeonBorder } from '../components/common/NeonBorder';
import { ParticleBackground } from '../components/common/ParticleBackground';
import { CyberGrid } from '../components/common/CyberGrid';
import { Scanline } from '../components/common/Scanline';
import { useBilling } from '../hooks/useBilling';

const VERIFICATION_TIERS = [
    {
        id: 'blue',
        name: 'Verified',
        price: 9.99,
        color: '#06b6d4',
        icon: FiCheck,
        features: [
            'Blue checkmark on profile',
            'Boosted in search (+15%)',
            'Real name displayed',
            'Prevents impersonation',
        ],
    },
    {
        id: 'purple',
        name: 'Premium Verified',
        price: 29.99,
        color: '#a855f7',
        icon: FiAward,
        popular: true,
        features: [
            'Purple checkmark',
            'Boosted in search (+35%)',
            'Featured in discover',
            'Priority support',
            'Verified badge on all platforms',
        ],
    },
    {
        id: 'gold',
        name: 'Elite',
        price: 99.99,
        color: '#eab308',
        icon: FiStar,
        features: [
            'Gold checkmark',
            'Top of search results (+75%)',
            'Homepage feature',
            'Direct support line',
            'Custom profile URL',
            'QR code for business cards',
        ],
    },
];

const BOOST_PACKAGES = [
    {
        id: 'starter',
        name: 'Starter Boost',
        price: 4.99,
        duration: '7 days',
        boost: '+25%',
        color: '#06b6d4',
        icon: FiZap,
    },
    {
        id: 'standard',
        name: 'Standard Boost',
        price: 14.99,
        duration: '30 days',
        boost: '+50%',
        color: '#a855f7',
        icon: FiTrendingUp,
        popular: true,
    },
    {
        id: 'premium',
        name: 'Premium Boost',
        price: 49.99,
        duration: '90 days',
        boost: '+100%',
        color: '#ec4899',
        icon: FiStar,
    },
];

export const VerficationsPage: React.FC = () => {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState<'verification' | 'boosts'>('verification');
    const { buyVerification, buyBoost, isPurchasing } = useBilling();

    return (
        <div className="relative min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 py-8 px-4 overflow-x-hidden">
            <ParticleBackground />
            <CyberGrid animated speed={0.3} />
            <Scanline color="#a855f7" intensity={0.3} />

            <motion.header
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="relative z-10 max-w-6xl mx-auto mb-8"
            >
                <button
                    onClick={() => navigate(-1)}
                    className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all text-sm text-gray-300 hover:text-white font-mono group mb-6"
                >
                    <FiArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
                    Back
                </button>

                <div className="text-center">
                    <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30 flex items-center justify-center">
                        <FiShield className="w-8 h-8 text-purple-400" />
                    </div>
                    <h1 className="text-3xl sm:text-4xl font-bold text-white mb-2">
                        <span className="shimmer-text">Stand Out</span>
                    </h1>
                    <p className="text-sm text-gray-400 font-mono">
                        Verification badges and profile boosts
                    </p>
                </div>

                <div className="flex justify-center mt-6">
                    <div className="inline-flex items-center gap-1 p-1 bg-white/5 rounded-full border border-white/10">
                        {[
                            { id: 'verifications', label: 'Verifications', icon: FiAward },
                            { id: 'boosts', label: 'Profile Boosts', icon: FiZap },
                        ].map((tab) => {
                            const Icon = tab.icon;
                            return (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id as any)}
                                    className={`flex items-center gap-2 px-5 py-2 rounded-full text-xs font-mono uppercase tracking-wider transition-all ${activeTab === tab.id
                                        ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg'
                                        : 'text-gray-400 hover:text-white'
                                        }`}
                                >
                                    <Icon className="w-3.5 h-3.5" />
                                    {tab.label}
                                </button>
                            );
                        })}
                    </div>
                </div>
            </motion.header>

            <motion.main
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="relative z-10 max-w-6xl mx-auto"
            >
                {activeTab === 'verification' && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {VERIFICATION_TIERS.map((tier) => {
                            const Icon = tier.icon;
                            const isPopular = tier.popular;

                            return (
                                <motion.div
                                    key={tier.id}
                                    initial={{ opacity: 0, y: 30 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={isPopular ? 'md:-mt-4 md:mb-4' : ''}
                                >
                                    {isPopular ? (
                                        <NeonBorder color="purple" intensity="high">
                                            <div className="p-6 sm:p-8 relative">
                                                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full text-[10px] font-bold text-white font-mono uppercase tracking-wider shadow-lg">
                                                    Best Value
                                                </div>

                                                <div
                                                    className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
                                                    style={{
                                                        background: `linear-gradient(135deg, ${tier.color}20, ${tier.color}05)`,
                                                        border: `1px solid ${tier.color}30`,
                                                    }}
                                                >
                                                    <Icon className="w-7 h-7" style={{ color: tier.color }} />
                                                </div>

                                                <h3 className="text-2xl font-bold text-white mb-1">
                                                    {tier.name}
                                                </h3>
                                                <div className="flex items-baseline gap-1 mb-6">
                                                    <span
                                                        className="text-4xl font-black font-mono"
                                                        style={{ color: tier.color }}
                                                    >
                                                        ${tier.price}
                                                    </span>
                                                    <span className="text-xs text-gray-500 font-mono">
                                                        one-time
                                                    </span>
                                                </div>

                                                <ul className="space-y-2 mb-6">
                                                    {tier.features.map((feature, i) => (
                                                        <li
                                                            key={i}
                                                            className="flex items-start gap-2 text-sm text-gray-300"
                                                        >
                                                            <FiCheck className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                                                            <span>{feature}</span>
                                                        </li>
                                                    ))}
                                                </ul>

                                                <GradientButton
                                                    onClick={() => buyVerification(tier.id)}
                                                    disabled={isPurchasing}
                                                    loading={isPurchasing}
                                                    variant="rainbow"
                                                    size="lg"
                                                    fullWidth
                                                    pulse
                                                >
                                                    Get {tier.name}
                                                </GradientButton>
                                            </div>
                                        </NeonBorder>
                                    ) : (
                                        <GlassCard variant="dark" padding="none" className="h-full">
                                            <div className="p-6 sm:p-8">
                                                <div
                                                    className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
                                                    style={{
                                                        background: `linear-gradient(135deg, ${tier.color}20, ${tier.color}05)`,
                                                        border: `1px solid ${tier.color}30`,
                                                    }}
                                                >
                                                    <Icon className="w-7 h-7" style={{ color: tier.color }} />
                                                </div>

                                                <h3 className="text-2xl font-bold text-white mb-1">
                                                    {tier.name}
                                                </h3>
                                                <div className="flex items-baseline gap-1 mb-6">
                                                    <span
                                                        className="text-4xl font-black font-mono"
                                                        style={{ color: tier.color }}
                                                    >
                                                        ${tier.price}
                                                    </span>
                                                    <span className="text-xs text-gray-500 font-mono">
                                                        one-time
                                                    </span>
                                                </div>

                                                <ul className="space-y-2 mb-6">
                                                    {tier.features.map((feature, i) => (
                                                        <li
                                                            key={i}
                                                            className="flex items-start gap-2 text-sm text-gray-300"
                                                        >
                                                            <FiCheck className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                                                            <span>{feature}</span>
                                                        </li>
                                                    ))}
                                                </ul>

                                                <GradientButton
                                                    onClick={() => buyVerification(tier.id)}
                                                    disabled={isPurchasing}
                                                    loading={isPurchasing}
                                                    variant="cyan"
                                                    size="lg"
                                                    fullWidth
                                                >
                                                    Get {tier.name}
                                                </GradientButton>
                                            </div>
                                        </GlassCard>
                                    )}
                                </motion.div>
                            );
                        })}
                    </div>
                )}

                {activeTab === 'boosts' && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {BOOST_PACKAGES.map((pkg) => {
                            const Icon = pkg.icon;
                            const isPopular = pkg.popular;

                            return (
                                <motion.div
                                    key={pkg.id}
                                    initial={{ opacity: 0, y: 30 }}
                                    animate={{ opacity: 1, y: 0 }}
                                >
                                    {isPopular ? (
                                        <NeonBorder color="purple" intensity="high">
                                            <div className="p-6 sm:p-8">
                                                <div
                                                    className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
                                                    style={{
                                                        background: `linear-gradient(135deg, ${pkg.color}20, ${pkg.color}05)`,
                                                        border: `1px solid ${pkg.color}30`,
                                                    }}
                                                >
                                                    <Icon className="w-7 h-7" style={{ color: pkg.color }} />
                                                </div>

                                                <h3 className="text-2xl font-bold text-white mb-1">
                                                    {pkg.name}
                                                </h3>
                                                <div className="flex items-baseline gap-1 mb-2">
                                                    <span
                                                        className="text-4xl font-black font-mono"
                                                        style={{ color: pkg.color }}
                                                    >
                                                        ${pkg.price}
                                                    </span>
                                                    <span className="text-xs text-gray-500 font-mono">
                                                        /{pkg.duration}
                                                    </span>
                                                </div>
                                                <div
                                                    className="inline-block px-3 py-1 rounded-lg mb-6 text-xs font-bold font-mono"
                                                    style={{
                                                        backgroundColor: `${pkg.color}20`,
                                                        color: pkg.color,
                                                    }}
                                                >
                                                    {pkg.boost} ranking boost
                                                </div>

                                                <GradientButton
                                                    onClick={() => buyBoost(pkg.id)}
                                                    disabled={isPurchasing}
                                                    loading={isPurchasing}
                                                    variant="rainbow"
                                                    size="lg"
                                                    fullWidth
                                                    pulse
                                                >
                                                    Buy Boost
                                                </GradientButton>
                                            </div>
                                        </NeonBorder>
                                    ) : (
                                        <GlassCard variant="dark" padding="none" className="h-full">
                                            <div className="p-6 sm:p-8">
                                                <div
                                                    className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
                                                    style={{
                                                        background: `linear-gradient(135deg, ${pkg.color}20, ${pkg.color}05)`,
                                                        border: `1px solid ${pkg.color}30`,
                                                    }}
                                                >
                                                    <Icon className="w-7 h-7" style={{ color: pkg.color }} />
                                                </div>

                                                <h3 className="text-2xl font-bold text-white mb-1">
                                                    {pkg.name}
                                                </h3>
                                                <div className="flex items-baseline gap-1 mb-2">
                                                    <span
                                                        className="text-4xl font-black font-mono"
                                                        style={{ color: pkg.color }}
                                                    >
                                                        ${pkg.price}
                                                    </span>
                                                    <span className="text-xs text-gray-500 font-mono">
                                                        /{pkg.duration}
                                                    </span>
                                                </div>
                                                <div
                                                    className="inline-block px-3 py-1 rounded-lg mb-6 text-xs font-bold font-mono"
                                                    style={{
                                                        backgroundColor: `${pkg.color}20`,
                                                        color: pkg.color,
                                                    }}
                                                >
                                                    {pkg.boost} ranking boost
                                                </div>

                                                <GradientButton
                                                    onClick={() => buyBoost(pkg.id)}
                                                    disabled={isPurchasing}
                                                    loading={isPurchasing}
                                                    variant="cyan"
                                                    size="lg"
                                                    fullWidth
                                                >
                                                    Buy Boost
                                                </GradientButton>
                                            </div>
                                        </GlassCard>
                                    )}
                                </motion.div>
                            );
                        })}
                    </div>
                )}
            </motion.main>
        </div>
    );
};

export default VerficationsPage;
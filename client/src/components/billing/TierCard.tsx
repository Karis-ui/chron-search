import React from 'react';
import { motion } from 'framer-motion';
import {
    FiCheck,
    FiX,
    FiZap,
    FiStar,
    FiBriefcase,
    FiCompass,
    FiTrendingUp,
} from 'react-icons/fi';

import { GlassCard } from '../common/GlassCard';
import { GradientButton } from '../common/GradientButton';
import { NeonBorder } from '../common/NeonBorder';


const TIER_ICONS: Record<string, any> = {
    free: FiCompass,
    pro: FiStar,
    ultra: FiZap,
    enterprise: FiBriefcase,
};

const TIER_COLORS: Record<string, string> = {
    free: '#06b6d4',
    pro: '#a855f7',
    ultra: '#ec4899',
    enterprise: '#22c55e',
};

export interface TierCardProps {
    tier: {
        id: string;
        name: string;
        description: string;
        price_monthly: number;
        price_yearly: number;
        limits: Record<string, any>;
    };
    billingCycle: 'monthly' | 'yearly';
    currentTier?: string;
    isPopular?: boolean;
    onSelect: (tierId: string) => void;
    isProcessing?: boolean;
}

export const TierCard: React.FC<TierCardProps> = ({
    tier,
    billingCycle,
    currentTier,
    isPopular = false,
    onSelect,
    isProcessing = false,
}) => {
    const Icon = TIER_ICONS[tier.id] || FiCompass;
    const color = TIER_COLORS[tier.id] || '#06b6d4';
    const isCurrent = currentTier === tier.id;
    const price = billingCycle === 'monthly' ? tier.price_monthly : tier.price_yearly;
    const isEnterprise = tier.id === 'enterprise';

    const features = [
        {
            label:
                tier.limits.searches_per_day === -1
                    ? 'Unlimited searches'
                    : `${tier.limits.searches_per_day} searches/day`,
            included: true,
        },
        {
            label:
                tier.limits.platforms_count === 'all'
                    ? 'All 12 platforms'
                    : `${tier.limits.platforms_count} platforms`,
            included: true,
        },
        {
            label: `${tier.limits.time_range_days}-day history`,
            included: true,
        },
        {
            label: 'Voice recognition',
            included: !!tier.limits.voice_recognition,
        },
        {
            label: 'Batch search',
            included: !!tier.limits.batch_search,
        },
        {
            label: 'Advanced filters',
            included: !!tier.limits.advanced_filters,
        },
        {
            label:
                tier.limits.export_formats?.length > 0
                    ? `Export ${tier.limits.export_formats.join(', ').toUpperCase()}`
                    : 'No export',
            included: tier.limits.export_formats?.length > 0,
        },
        {
            label:
                tier.limits.saved_searches === -1
                    ? 'Unlimited saved searches'
                    : `${tier.limits.saved_searches} saved searches`,
            included: tier.limits.saved_searches > 0,
        },
        {
            label: 'Alerts',
            included: !!tier.limits.alerts_enabled,
        },
        {
            label:
                tier.limits.api_calls_per_month === -1
                    ? 'Unlimited API'
                    : tier.limits.api_calls_per_month > 0
                        ? `${tier.limits.api_calls_per_month.toLocaleString()} API calls`
                        : 'No API access',
            included: tier.limits.api_calls_per_month !== 0,
        },
        {
            label: 'Priority support',
            included: !!tier.limits.priority_support,
        },
    ];

    const cardContent = (
        <div className="relative p-6 sm:p-8 h-full flex flex-col">
            {isPopular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full text-[10px] font-bold text-white font-mono uppercase tracking-wider shadow-lg z-10 flex items-center gap-1.5">
                    <FiTrendingUp className="w-3 h-3" />
                    Most Popular
                </div>
            )}
            <div className="mb-6">
                <div
                    className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
                    style={{
                        background: `linear-gradient(135deg, ${color}20, ${color}05)`,
                        border: `1px solid ${color}30`,
                    }}
                >
                    <Icon className="w-6 h-6" style={{ color }} />
                </div>

                <h3 className="text-2xl font-bold text-white mb-1">{tier.name}</h3>
                <p className="text-sm text-gray-400">{tier.description}</p>
            </div>

            {/* Price */}
            <div className="mb-6 pb-6 border-b border-white/5">
                {isEnterprise ? (
                    <div className="text-3xl font-bold" style={{ color }}>
                        Custom
                    </div>
                ) : (
                    <>
                        <div className="flex items-baseline gap-2">
                            <span
                                className="text-4xl sm:text-5xl font-black font-mono"
                                style={{ color }}
                            >
                                ${price}
                            </span>
                            <span className="text-sm text-gray-500 font-mono">
                                /{billingCycle === 'monthly' ? 'mo' : 'yr'}
                            </span>
                        </div>
                        {billingCycle === 'yearly' && price > 0 && (
                            <p className="text-xs text-green-400 font-mono mt-1">
                                Save ${tier.price_monthly * 12 - price}/year
                            </p>
                        )}
                    </>
                )}
            </div>

            <div className="space-y-3 mb-6 flex-1">
                {features.map((feature, idx) => (
                    <div key={idx} className="flex items-start gap-2">
                        {feature.included ? (
                            <FiCheck className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                        ) : (
                            <FiX className="w-4 h-4 text-gray-600 flex-shrink-0 mt-0.5" />
                        )}
                        <span
                            className={`text-sm ${feature.included ? 'text-gray-300' : 'text-gray-600 line-through'
                                }`}
                        >
                            {feature.label}
                        </span>
                    </div>
                ))}
            </div>

            <GradientButton
                onClick={() => onSelect(tier.id)}
                disabled={isCurrent || isProcessing}
                loading={isProcessing}
                loadingText="Redirecting..."
                variant={isPopular ? 'rainbow' : isCurrent ? 'ghost' : 'cyan'}
                size="lg"
                fullWidth
                pulse={isPopular && !isCurrent}
            >
                {isCurrent ? (
                    <>
                        <FiCheck className="w-4 h-4" />
                        Current Plan
                    </>
                ) : isEnterprise ? (
                    'Contact Sales'
                ) : (
                    `Upgrade to ${tier.name}`
                )}
            </GradientButton>
        </div>
    );

    return (
        <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className={`relative ${isPopular ? 'md:-mt-4 md:mb-4' : ''}`}
        >
            {isPopular ? (
                <NeonBorder color="purple" intensity="high" animationSpeed={0.5}>
                    {cardContent}
                </NeonBorder>
            ) : (
                <GlassCard
                    variant="dark"
                    hover
                    hoverEffect="lift"
                    padding="none"
                    className="relative h-full"
                >
                    {cardContent}
                </GlassCard>
            )}
        </motion.div>
    );
};

export default TierCard;
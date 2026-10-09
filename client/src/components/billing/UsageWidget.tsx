import React from 'react';
import { motion } from 'framer-motion';
import {
    FiTrendingUp,
    FiAlertCircle,
    FiArrowUpRight,
    FiSearch,
    FiCpu,
    FiClock,
} from 'react-icons/fi';
import type { IconType } from 'react-icons';
import { Link } from 'react-router-dom';

import { GlassCard } from '../common/GlassCard';
import { useBilling } from '../../hooks/useBilling';
import { ROUTES } from '../../constants/routes';

interface UsageWidgetProps {
    variant?: 'inline' | 'panel' | 'full';
}

export const UsageWidget: React.FC<UsageWidgetProps> = ({ variant = 'panel' }) => {
    const { capabilities, subscription, openUpgradeModal } = useBilling();

    if (!capabilities || !subscription) {
        return null;
    }

    const { usage, limits, tier, tier_name } = capabilities;

    const dailyPercent =
        limits.searches_per_day === -1
            ? 0
            : (usage.searches_today / limits.searches_per_day) * 100;

    const monthlyPercent =
        limits.searches_per_month === -1
            ? 0
            : (usage.searches_this_month / limits.searches_per_month) * 100;

    const apiPercent =
        limits.api_calls_per_month <= 0
            ? 0
            : (usage.api_calls_this_month / limits.api_calls_per_month) * 100;

    if (variant === 'inline') {
        const dailyRemaining = usage.daily_remaining;
        const isLow = dailyRemaining !== -1 && dailyRemaining <= 2;
        const color =
            dailyRemaining === -1 ? '#22c55e' : isLow ? '#f87171' : '#06b6d4';

        return (
            <Link
                to={ROUTES.BILLING}
                className="inline-flex items-center gap-2 px-3 py-1.5 bg-white/5 backdrop-blur-xl rounded-full border border-white/10 hover:border-white/20 transition-all group"
            >
                <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />
                <span className="text-[10px] font-mono text-gray-400 group-hover:text-white transition-colors">
                    {dailyRemaining === -1 ? 'Unlimited' : `${dailyRemaining} left today`}
                </span>
                <span
                    className="text-[9px] font-mono font-bold uppercase px-1.5 py-0.5 rounded"
                    style={{ backgroundColor: `${color}20`, color }}
                >
                    {tier_name}
                </span>
            </Link>
        );
    }

    if (variant === 'panel') {
        return (
            <GlassCard variant="dark" padding="md" glow="cyan" glowIntensity="low">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                        <FiTrendingUp className="w-4 h-4 text-cyan-400" />
                        <span className="text-xs font-semibold text-white">Usage</span>
                    </div>
                    <Link
                        to={ROUTES.BILLING}
                        className="text-[10px] text-cyan-400 hover:text-cyan-300 font-mono transition-colors flex items-center gap-1"
                    >
                        {tier_name}
                        <FiArrowUpRight className="w-3 h-3" />
                    </Link>
                </div>

                <div className="space-y-3">
                    <div>
                        <div className="flex items-center justify-between text-[10px] mb-1 font-mono">
                            <span className="text-gray-500 flex items-center gap-1">
                                <FiSearch className="w-2.5 h-2.5" />
                                Today
                            </span>
                            <span className={dailyPercent > 80 ? 'text-red-400' : 'text-gray-400'}>
                                {limits.searches_per_day === -1
                                    ? '∞'
                                    : `${usage.searches_today}/${limits.searches_per_day}`}
                            </span>
                        </div>
                        {limits.searches_per_day !== -1 && (
                            <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                                <motion.div
                                    className="h-full rounded-full"
                                    style={{
                                        backgroundColor:
                                            dailyPercent > 80
                                                ? '#f87171'
                                                : dailyPercent > 50
                                                    ? '#facc15'
                                                    : '#06b6d4',
                                    }}
                                    initial={{ width: 0 }}
                                    animate={{ width: `${Math.min(dailyPercent, 100)}%` }}
                                    transition={{ duration: 0.5 }}
                                />
                            </div>
                        )}
                    </div>

                    <div>
                        <div className="flex items-center justify-between text-[10px] mb-1 font-mono">
                            <span className="text-gray-500 flex items-center gap-1">
                                <FiClock className="w-2.5 h-2.5" />
                                Month
                            </span>
                            <span className={monthlyPercent > 80 ? 'text-red-400' : 'text-gray-400'}>
                                {limits.searches_per_month === -1
                                    ? '∞'
                                    : `${usage.searches_this_month}/${limits.searches_per_month}`}
                            </span>
                        </div>
                        {limits.searches_per_month !== -1 && (
                            <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                                <motion.div
                                    className="h-full rounded-full"
                                    style={{
                                        backgroundColor:
                                            monthlyPercent > 80
                                                ? '#f87171'
                                                : monthlyPercent > 50
                                                    ? '#facc15'
                                                    : '#a855f7',
                                    }}
                                    initial={{ width: 0 }}
                                    animate={{ width: `${Math.min(monthlyPercent, 100)}%` }}
                                    transition={{ duration: 0.5 }}
                                />
                            </div>
                        )}
                    </div>
                </div>

                {tier === 'free' && (
                    <button
                        onClick={() => openUpgradeModal("upgrade")}
                        className="w-full mt-4 py-2 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 hover:from-cyan-500/30 hover:to-purple-500/30 border border-cyan-500/30 rounded-lg text-[10px] font-mono font-semibold text-cyan-400 transition-all"
                    >
                        Upgrade for more
                    </button>
                )}
            </GlassCard>
        );
    }

    return (
        <div className="space-y-4">
            <GlassCard variant="dark" padding="lg" glow="cyan" glowIntensity="low">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h3 className="text-lg font-bold text-white mb-1">{tier_name} Plan</h3>
                        <p className="text-xs text-gray-500 font-mono">
                            Current usage for this billing period
                        </p>
                    </div>
                    <Link
                        to={ROUTES.BILLING}
                        className="px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded-lg border border-white/10 text-[10px] font-mono text-cyan-400 transition-all"
                    >
                        Manage →
                    </Link>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <UsageCard
                        icon={FiSearch}
                        label="Searches Today"
                        value={
                            limits.searches_per_day === -1
                                ? 'Unlimited'
                                : `${usage.searches_today} / ${limits.searches_per_day}`
                        }
                        color="#06b6d4"
                        percent={dailyPercent}
                    />
                    <UsageCard
                        icon={FiTrendingUp}
                        label="Searches This Month"
                        value={
                            limits.searches_per_month === -1
                                ? 'Unlimited'
                                : `${usage.searches_this_month} / ${limits.searches_per_month}`
                        }
                        color="#a855f7"
                        percent={monthlyPercent}
                    />
                    <UsageCard
                        icon={FiCpu}
                        label="API Calls"
                        value={
                            limits.api_calls_per_month === -1
                                ? 'Unlimited'
                                : limits.api_calls_per_month === 0
                                    ? 'Not available'
                                    : `${usage.api_calls_this_month} / ${limits.api_calls_per_month}`
                        }
                        color="#ec4899"
                        percent={apiPercent}
                    />
                </div>
            </GlassCard>

            {(dailyPercent > 80 || monthlyPercent > 80) && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-start gap-3 p-4 bg-yellow-500/5 border border-yellow-500/20 rounded-xl"
                >
                    <FiAlertCircle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                        <p className="text-xs text-yellow-400 font-semibold mb-1">
                            Approaching your limit
                        </p>
                        <p className="text-xs text-gray-400 mb-3">
                            You've used over 80% of your quota. Upgrade to avoid interruptions.
                        </p>
                        <button
                            onClick={() => openUpgradeModal("upgrade")}
                            className="text-xs text-cyan-400 hover:text-cyan-300 font-mono flex items-center gap-1 transition-colors"
                        >
                            Upgrade now
                            <FiArrowUpRight className="w-3 h-3" />
                        </button>
                    </div>
                </motion.div>
            )}
        </div>
    );
};

interface UsageCardProps {
    icon: IconType;
    label: string;
    value: string;
    color: string;
    percent: number;
}

const UsageCard: React.FC<UsageCardProps> = ({
    icon: Icon,
    label,
    value,
    color,
    percent,
}) => (
    <div className="p-3 bg-white/5 rounded-xl border border-white/5">
        <div className="flex items-center gap-2 mb-2">
            <div
                className="w-7 h-7 rounded-lg flex items-center justify-center"
                style={{
                    background: `linear-gradient(135deg, ${color}20, ${color}05)`,
                    border: `1px solid ${color}30`,
                }}
            >
                <Icon className="w-3.5 h-3.5" style={{ color }} />
            </div>
            <span className="text-[10px] text-gray-500 font-mono uppercase tracking-wider">
                {label}
            </span>
        </div>
        <p className="text-sm font-bold text-white font-mono">{value}</p>
        {percent > 0 && (
            <div className="mt-2 h-1 bg-white/5 rounded-full overflow-hidden">
                <motion.div
                    className="h-full rounded-full"
                    style={{ backgroundColor: color }}
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(percent, 100)}%` }}
                    transition={{ duration: 0.5 }}
                />
            </div>
        )}
    </div>
);

export default UsageWidget;
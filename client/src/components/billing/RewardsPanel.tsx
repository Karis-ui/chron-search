import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
    FiDollarSign,
    FiTrendingUp,
    FiClock,
    FiArrowUpRight,
    FiExternalLink,
    FiCheck,
    FiAlertCircle,
    FiRefreshCw,
    FiDownload,
} from 'react-icons/fi';

import { GlassCard } from '../common/GlassCard';
import { GradientButton } from '../common/GradientButton';
import { NeonBorder } from '../common/NeonBorder';
import { useBilling } from '../../hooks/useBilling';
import rewardsApi from '../../api/endpoints/rewards';

export const RewardsPanel: React.FC = () => {
    const {
        balance,
        requestPayout,
        isRequestingPayout,
        isConnectingStripe,
        startConnect,
    } = useBilling();
    const [showPayoutModal, setShowPayoutModal] = useState(false);
    const [payoutAmount, setPayoutAmount] = useState('');
    const ledgerQuery = useQuery({
        queryKey: ['rewards', 'ledger'],
        queryFn: () => rewardsApi.getLedger(10, 0),
    });
    const connectQuery = useQuery({
        queryKey: ['rewards', 'connect-status'],
        queryFn: rewardsApi.getConnectStatus,
    });
    const earningsQuery = useQuery({
        queryKey: ['rewards', 'earnings'],
        queryFn: rewardsApi.getEarnings,
    });
    const payoutsQuery = useQuery({
        queryKey: ['rewards', 'payouts'],
        queryFn: () => rewardsApi.getPayouts(20),
    });
    if (!balance) {
        return (
            <GlassCard variant="dark" padding="lg">
                <div className="text-center py-8">
                    <div className="w-10 h-10 border-2 border-cyan-400 border-t-transparent rounded-full mx-auto animate-spin mb-3" />
                    <p className="text-sm text-gray-500 font-mono">
                        Loading rewards...
                    </p>
                </div>
            </GlassCard>
        );
    }

    const connectStatus = connectQuery.data;
    const needsOnboarding = connectStatus && (!connectStatus.has_account || !connectStatus.onboarding_complete);
    const handlePayout = () => {
        const amount = payoutAmount ? parseFloat(payoutAmount) : undefined;
        requestPayout(amount);
        setShowPayoutModal(false);
        setPayoutAmount('');
    }
    return (
        <div className="space-y-6">
            <NeonBorder color="green" intensity="high" animationSpeed={0.6}>
                <div className="relative p-6 sm:p-8 overflow-hidden">
                    <div
                        className="absolute -top-20 -right-20 w-60 h-60 rounded-full pointer-events-none"
                        style={{
                            background:
                                'radial-gradient(circle, rgba(34,197,94,0.15) 0%, transparent 70%)',
                        }}
                    />

                    <div className="relative">
                        <div className="flex items-center gap-2 mb-4">
                            <div className="w-10 h-10 rounded-xl bg-green-500/20 border border-green-500/30 flex items-center justify-center">
                                <FiDollarSign className="w-5 h-5 text-green-400" />
                            </div>
                            <div>
                                <p className="text-[10px] text-gray-500 font-mono uppercase tracking-wider">
                                    Available Balance
                                </p>
                                <p className="text-xs text-gray-400">Ready to withdraw</p>
                            </div>
                        </div>

                        <div className="flex flex-wrap items-baseline gap-3 mb-6">
                            <span className="text-5xl sm:text-6xl font-black text-white font-mono">
                                ${balance.available.toFixed(2)}
                            </span>
                            <span className="text-sm text-gray-500 font-mono">USD</span>
                        </div>

                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
                            <MiniStat
                                icon={FiClock}
                                label="Pending"
                                value={`$${balance.pending.toFixed(2)}`}
                                color="#facc15"
                            />
                            <MiniStat
                                icon={FiTrendingUp}
                                label="This Month"
                                value={`$${balance.monthly_earned.toFixed(2)}`}
                                color="#06b6d4"
                            />
                            <MiniStat
                                icon={FiDollarSign}
                                label="Lifetime"
                                value={`$${balance.lifetime_earned.toFixed(2)}`}
                                color="#a855f7"
                            />
                            <MiniStat
                                icon={FiDownload}
                                label="Withdrawn"
                                value={`$${balance.lifetime_paid.toFixed(2)}`}
                                color="#22c55e"
                            />
                        </div>

                        {balance.monthly_cap > 0 && (
                            <div className="mb-6">
                                <div className="flex items-center justify-between text-[10px] font-mono mb-1.5">
                                    <span className="text-gray-500">
                                        Monthly cap: ${balance.monthly_cap}
                                    </span>
                                    <span className="text-gray-400">
                                        {(
                                            (balance.monthly_earned / balance.monthly_cap) *
                                            100
                                        ).toFixed(0)}
                                        % used
                                    </span>
                                </div>
                                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                                    <motion.div
                                        className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full"
                                        initial={{ width: 0 }}
                                        animate={{
                                            width: `${Math.min(
                                                (balance.monthly_earned / balance.monthly_cap) * 100,
                                                100
                                            )}%`,
                                        }}
                                        transition={{ duration: 0.8 }}
                                    />
                                </div>
                            </div>
                        )}

                        <div className="flex flex-wrap gap-3">
                            {needsOnboarding ? (
                                <GradientButton
                                    onClick={startConnect}
                                    loading={isConnectingStripe}
                                    loadingText="Opening Stripe..."
                                    variant="rainbow"
                                    size="lg"
                                    icon={<FiExternalLink />}
                                    iconPosition="right"
                                >
                                    Set Up Payout Account
                                </GradientButton>
                            ) : balance.can_withdraw ? (
                                <GradientButton
                                    onClick={() => setShowPayoutModal(true)}
                                    variant="rainbow"
                                    size="lg"
                                    pulse
                                    icon={<FiArrowUpRight />}
                                    iconPosition="right"
                                >
                                    Withdraw ${balance.available.toFixed(2)}
                                </GradientButton>
                            ) : (
                                <div className="flex items-center gap-2 px-4 py-3 bg-white/5 rounded-xl border border-white/10">
                                    <FiAlertCircle className="w-4 h-4 text-yellow-400" />
                                    <span className="text-xs text-gray-400 font-mono">
                                        Minimum payout: ${balance.minimum_payout.toFixed(2)}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </NeonBorder>

            {earningsQuery.data && (
                <GlassCard variant="dark" padding="lg">
                    <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/5">
                        <FiTrendingUp className="w-4 h-4 text-cyan-400" />
                        <h3 className="text-sm font-semibold text-white">
                            Earnings Breakdown
                        </h3>
                    </div>

                    <div className="space-y-3">
                        {Object.entries(earningsQuery.data.breakdown).map(([type, data]) => (
                            <div
                                key={type}
                                className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/5"
                            >
                                <div className="flex items-center gap-3">
                                    <div className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                                    <div>
                                        <p className="text-xs text-white font-medium capitalize">
                                            {type.replace('_', ' ')}
                                        </p>
                                        <p className="text-[10px] text-gray-500 font-mono">
                                            {data.count} {data.count === 1 ? 'time' : 'times'}
                                        </p>
                                    </div>
                                </div>
                                <span className="text-sm font-bold text-green-400 font-mono">
                                    ${data.total.toFixed(2)}
                                </span>
                            </div>
                        ))}
                    </div>
                </GlassCard>
            )}

            <GlassCard variant="dark" padding="lg">
                <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/5">
                    <div className="flex items-center gap-2">
                        <FiClock className="w-4 h-4 text-cyan-400" />
                        <h3 className="text-sm font-semibold text-white">
                            Recent Rewards
                        </h3>
                    </div>
                    <button
                        onClick={() => ledgerQuery.refetch()}
                        className="p-1.5 hover:bg-white/5 rounded-lg transition-colors"
                    >
                        <FiRefreshCw
                            className={`w-3.5 h-3.5 text-gray-500 ${ledgerQuery.isFetching ? 'animate-spin' : ''
                                }`}
                        />
                    </button>
                </div>

                {ledgerQuery.data?.entries && ledgerQuery.data.entries.length > 0 ? (
                    <div className="space-y-2">
                        {ledgerQuery.data.entries.map((entry) => (
                            <div
                                key={entry.id}
                                className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/5"
                            >
                                <div className="flex items-center gap-3 flex-1 min-w-0">
                                    <div
                                        className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${entry.status === 'confirmed' || entry.status === 'paid'
                                                ? 'bg-green-500/20 border border-green-500/30'
                                                : entry.status === 'pending'
                                                    ? 'bg-yellow-500/20 border border-yellow-500/30'
                                                    : 'bg-red-500/20 border border-red-500/30'
                                            }`}
                                    >
                                        {entry.status === 'confirmed' || entry.status === 'paid' ? (
                                            <FiCheck className="w-4 h-4 text-green-400" />
                                        ) : entry.status === 'pending' ? (
                                            <FiClock className="w-4 h-4 text-yellow-400" />
                                        ) : (
                                            <FiAlertCircle className="w-4 h-4 text-red-400" />
                                        )}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-xs text-white font-medium truncate">
                                            {entry.description || entry.type.replace('_', ' ')}
                                        </p>
                                        <p className="text-[10px] text-gray-500 font-mono">
                                            {new Date(entry.created_at).toLocaleString()}
                                        </p>
                                    </div>
                                </div>
                                <div className="text-right flex-shrink-0">
                                    <p className="text-sm font-bold text-green-400 font-mono">
                                        +${entry.amount.toFixed(2)}
                                    </p>
                                    <p className="text-[10px] text-gray-500 font-mono uppercase">
                                        {entry.status}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-8">
                        <FiDollarSign className="w-8 h-8 text-gray-600 mx-auto mb-2" />
                        <p className="text-xs text-gray-500">No rewards yet</p>
                        <p className="text-[10px] text-gray-600 mt-1">
                            Get found in searches to start earning
                        </p>
                    </div>
                )}
            </GlassCard>

            {payoutsQuery.data && payoutsQuery.data.length > 0 && (
                <GlassCard variant="dark" padding="lg">
                    <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/5">
                        <FiDownload className="w-4 h-4 text-cyan-400" />
                        <h3 className="text-sm font-semibold text-white">
                            Payout History
                        </h3>
                    </div>

                    <div className="space-y-2">
                        {payoutsQuery.data.map((payout) => (
                            <div
                                key={payout.id}
                                className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/5"
                            >
                                <div className="flex items-center gap-3">
                                    <div
                                        className={`w-8 h-8 rounded-lg flex items-center justify-center ${payout.status === 'paid'
                                                ? 'bg-green-500/20 border border-green-500/30'
                                                : payout.status === 'failed'
                                                    ? 'bg-red-500/20 border border-red-500/30'
                                                    : 'bg-yellow-500/20 border border-yellow-500/30'
                                            }`}
                                    >
                                        {payout.status === 'paid' ? (
                                            <FiCheck className="w-4 h-4 text-green-400" />
                                        ) : (
                                            <FiClock className="w-4 h-4 text-yellow-400" />
                                        )}
                                    </div>
                                    <div>
                                        <p className="text-xs text-white font-medium">
                                            Payout
                                        </p>
                                        <p className="text-[10px] text-gray-500 font-mono">
                                            {new Date(payout.requested_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <p className="text-sm font-bold text-white font-mono">
                                        ${payout.amount.toFixed(2)}
                                    </p>
                                    <p className="text-[10px] text-gray-500 font-mono uppercase">
                                        {payout.status}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </GlassCard>
            )}

            <AnimatePresence>
                {showPayoutModal && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setShowPayoutModal(false)}
                            className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-xl"
                        />
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.9 }}
                            className="fixed inset-0 z-[101] flex items-center justify-center p-4 pointer-events-none"
                        >
                            <div className="relative w-full max-w-md bg-gray-950 border border-green-500/30 rounded-3xl p-6 pointer-events-auto">
                                <h3 className="text-lg font-bold text-white mb-2">
                                    Request Payout
                                </h3>
                                <p className="text-xs text-gray-400 mb-4">
                                    Funds arrive in 1-3 business days
                                </p>

                                <div className="mb-4">
                                    <label className="block text-[10px] text-gray-500 font-mono uppercase tracking-wider mb-2">
                                        Amount (USD)
                                    </label>
                                    <div className="relative">
                                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 font-mono">
                                            $
                                        </span>
                                        <input
                                            type="number"
                                            value={payoutAmount}
                                            onChange={(e) => setPayoutAmount(e.target.value)}
                                            placeholder={balance.available.toFixed(2)}
                                            step="0.01"
                                            min={balance.minimum_payout}
                                            max={balance.available}
                                            className="w-full pl-7 pr-3 py-3 bg-white/5 border border-white/10 rounded-xl text-sm text-white font-mono focus:outline-none focus:border-green-500/50"
                                        />
                                    </div>
                                    <p className="text-[10px] text-gray-500 font-mono mt-1">
                                        Max: ${balance.available.toFixed(2)}
                                    </p>
                                </div>

                                <div className="flex items-center gap-3">
                                    <button
                                        onClick={() => setShowPayoutModal(false)}
                                        className="flex-1 px-4 py-3 bg-white/5 hover:bg-white/10 rounded-xl border border-white/10 text-sm text-gray-300 font-mono"
                                    >
                                        Cancel
                                    </button>
                                    <GradientButton
                                        onClick={handlePayout}
                                        loading={isRequestingPayout}
                                        loadingText="Processing..."
                                        variant="rainbow"
                                        size="md"
                                        className="flex-1"
                                    >
                                        Confirm Withdraw
                                    </GradientButton>
                                </div>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
};

const MiniStat: React.FC<{
    icon: any;
    label: string;
    value: string;
    color: string;
}> = ({ icon: Icon, label, value, color }) => (
    <div className="p-2.5 bg-white/5 rounded-xl border border-white/5">
        <div className="flex items-center gap-1.5 mb-1">
            <Icon className="w-2.5 h-2.5" style={{ color }} />
            <span className="text-[9px] text-gray-500 font-mono uppercase tracking-wider">
                {label}
            </span>
        </div>
        <p className="text-sm font-bold text-white font-mono">{value}</p>
    </div>
);

export default RewardsPanel;
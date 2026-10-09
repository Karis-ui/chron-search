import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    FiCreditCard,
    FiCalendar,
    FiCheck,
    FiExternalLink,
    FiAlertCircle,
    FiDownload,
    FiRefreshCw,
    FiZap,
} from 'react-icons/fi';

import { GlassCard } from '../common/GlassCard';
import { GradientButton } from '../common/GradientButton';
import { NeonBorder } from '../common/NeonBorder';
import { UsageWidget } from './UsageWidget';
import { useBilling } from '../../hooks/useBilling';
import { useQuery } from '@tanstack/react-query';
import billingApi from '../../api/endpoints/billing';

export const SubscriptionPanel: React.FC = () => {
    const {
        subscription,
        openPortal,
        cancelSubscription,
        resumeSubscription,
        isCancelling,
        isResuming,
    } = useBilling();
    const [showCancelConfirm, setShowCancelConfirm] = useState(false);
    const paymentsQuery = useQuery({
        queryKey: ['billing', 'payments'],
        queryFn: () => billingApi.getPayments(20),
    });

    if (!subscription) {
        return (
            <GlassCard className="text-center py-12">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-cyan-500 mx-auto"></div>
                <p className="mt-4 text-gray-400">Loading billing details...</p>
            </GlassCard>
        );
    }


    const isCancelling_pending = subscription.cancel_at_period_end;
    const isFree = subscription.tier === 'free';
    const formatDate = (date?: string) => {
        if (!date) return '--';
        return new Date(date).toLocaleDateString('em-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    };

    return (
        <div className="space-y-6">
            <NeonBorder
                color={isFree ? 'cyan' : 'purple'}
                intensity="medium"
            >
                <div className="p-6 sm:p-8">
                    <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
                        <div className="flex items-center gap-4">
                            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border border-cyan-500/30 flex items-center justify-center">
                                <FiZap className="w-7 h-7 text-cyan-400" />
                            </div>
                            <div>
                                <p className="text-[10px] text-gray-500 font-mono uppercase tracking-wider">
                                    Current Plan
                                </p>
                                <h2 className="text-2xl font-bold text-white">
                                    {subscription.tier_name}
                                </h2>
                                {!isFree && (
                                    <p className="text-xs text-gray-400 font-mono mt-0.5">
                                        ${subscription.amount}/{subscription.billing_cycle === 'monthly' ? 'mo' : 'yr'}
                                    </p>
                                )}
                            </div>
                        </div>

                        <div
                            className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-[10px] font-mono font-bold uppercase tracking-wider ${subscription.status === 'active' || subscription.status === 'trialing'
                                ? 'bg-green-500/10 border-green-500/30 text-green-400'
                                : 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
                                }`}
                        >
                            <div
                                className={`w-1.5 h-1.5 rounded-full ${subscription.status === 'active' || subscription.status === 'trialing'
                                    ? 'bg-green-400'
                                    : 'bg-yellow-400'
                                    } animate-pulse`}
                            />
                            {subscription.in_trial ? 'TRIAL' : subscription.status}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
                        <InfoBox
                            icon={FiCalendar}
                            label={subscription.cancel_at_period_end ? 'Ends' : 'Renews'}
                            value={formatDate(subscription.current_period_end)}
                            color={subscription.cancel_at_period_end ? '#f87171' : '#22c55e'}
                        />
                        <InfoBox
                            icon={FiCreditCard}
                            label="Total Spent"
                            value={`$${(paymentsQuery.data?.reduce((sum, p) => sum + p.amount, 0) || 0).toFixed(2)}`}
                            color="#06b6d4"
                        />
                        <InfoBox
                            icon={FiDownload}
                            label="Payments"
                            value={`${paymentsQuery.data?.length || 0}`}
                            color="#a855f7"
                        />
                    </div>

                    {isCancelling_pending && (
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex items-start gap-3 p-3 bg-yellow-500/5 border border-yellow-500/20 rounded-xl mb-4"
                        >
                            <FiAlertCircle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
                            <div className="flex-1">
                                <p className="text-xs text-yellow-400 font-semibold">
                                    Subscription ends on {formatDate(subscription.current_period_end)}
                                </p>
                                <p className="text-[10px] text-gray-500 mt-0.5">
                                    Resume anytime before then to keep your features.
                                </p>
                            </div>
                        </motion.div>
                    )}

                    <div className="flex flex-wrap gap-2">
                        {!isFree && (
                            <GradientButton
                                onClick={openPortal}
                                variant="cyan"
                                size="sm"
                                icon={<FiExternalLink />}
                            >
                                Manage Payment Method
                            </GradientButton>
                        )}

                        {isCancelling_pending ? (
                            <GradientButton
                                onClick={() => resumeSubscription()}
                                loading={isResuming}
                                variant="rainbow"
                                size="sm"
                                icon={<FiRefreshCw />}
                            >
                                Resume Subscription
                            </GradientButton>
                        ) : (
                            !isFree && (
                                <button
                                    onClick={() => setShowCancelConfirm(true)}
                                    className="px-4 py-2 bg-red-500/5 hover:bg-red-500/10 border border-red-500/20 hover:border-red-500/40 rounded-xl text-xs text-red-400 font-mono transition-all"
                                >
                                    Cancel Subscription
                                </button>
                            )
                        )}
                    </div>
                </div>
            </NeonBorder>

            <UsageWidget variant="full" />

            <GlassCard variant="dark" padding="lg">
                <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/5">
                    <div className="flex items-center gap-2">
                        <FiCreditCard className="w-4 h-4 text-cyan-400" />
                        <h3 className="text-sm font-semibold text-white">Payment History</h3>
                    </div>
                    <button
                        onClick={() => paymentsQuery.refetch()}
                        className="p-1.5 hover:bg-white/5 rounded-lg transition-colors"
                        title="Refresh"
                    >
                        <FiRefreshCw
                            className={`w-3.5 h-3.5 text-gray-500 ${paymentsQuery.isFetching ? 'animate-spin' : ''
                                }`}
                        />
                    </button>
                </div>

                {paymentsQuery.isLoading ? (
                    <div className="text-center py-8 text-xs text-gray-500 font-mono">
                        Loading...
                    </div>
                ) : paymentsQuery.data && paymentsQuery.data.length > 0 ? (
                    <div className="space-y-2">
                        {paymentsQuery.data.map((payment) => (
                            <div
                                key={payment.id}
                                className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/5"
                            >
                                <div className="flex items-center gap-3 flex-1 min-w-0">
                                    <div
                                        className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${payment.status === 'succeeded'
                                            ? 'bg-green-500/20 border border-green-500/30'
                                            : 'bg-yellow-500/20 border border-yellow-500/30'
                                            }`}
                                    >
                                        {payment.status === 'succeeded' ? (
                                            <FiCheck className="w-4 h-4 text-green-400" />
                                        ) : (
                                            <FiAlertCircle className="w-4 h-4 text-yellow-400" />
                                        )}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-xs text-white font-medium truncate">
                                            {payment.description || payment.type}
                                        </p>
                                        <p className="text-[10px] text-gray-500 font-mono">
                                            {new Date(payment.created_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                </div>
                                <div className="text-right flex-shrink-0">
                                    <p className="text-sm font-bold text-white font-mono">
                                        ${payment.amount.toFixed(2)}
                                    </p>
                                    <p className="text-[10px] text-gray-500 font-mono uppercase">
                                        {payment.currency}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-8">
                        <FiCreditCard className="w-8 h-8 text-gray-600 mx-auto mb-2" />
                        <p className="text-xs text-gray-500">No payments yet</p>
                    </div>
                )}
            </GlassCard>

            <AnimatePresence>
                {showCancelConfirm && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setShowCancelConfirm(false)}
                            className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-xl"
                        />
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.9 }}
                            className="fixed inset-0 z-[101] flex items-center justify-center p-4 pointer-events-none"
                        >
                            <div className="relative w-full max-w-md bg-gray-950 border border-red-500/30 rounded-3xl p-6 pointer-events-auto">
                                <div className="flex items-start gap-4 mb-4">
                                    <div className="w-12 h-12 rounded-2xl bg-red-500/20 border border-red-500/30 flex items-center justify-center flex-shrink-0">
                                        <FiAlertCircle className="w-6 h-6 text-red-400" />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold text-white mb-1">
                                            Cancel Subscription?
                                        </h3>
                                        <p className="text-sm text-gray-400">
                                            You'll keep access until the end of your billing period.
                                        </p>
                                    </div>
                                </div>

                                <div className="p-3 bg-white/5 rounded-xl mb-4">
                                    <p className="text-[10px] text-gray-500 font-mono">
                                        Active until:{' '}
                                        <span className="text-white">
                                            {formatDate(subscription.current_period_end)}
                                        </span>
                                    </p>
                                </div>

                                <div className="flex items-center gap-3">
                                    <button
                                        onClick={() => setShowCancelConfirm(false)}
                                        className="flex-1 px-4 py-3 bg-white/5 hover:bg-white/10 rounded-xl border border-white/10 text-sm text-gray-300 font-mono transition-colors"
                                    >
                                        Keep It
                                    </button>
                                    <button
                                        onClick={() => {
                                            cancelSubscription();
                                            setShowCancelConfirm(false);
                                        }}
                                        disabled={isCancelling}
                                        className="flex-1 px-4 py-3 bg-red-500/20 hover:bg-red-500/30 border border-red-500/40 rounded-xl text-sm text-red-400 font-mono font-semibold transition-colors disabled:opacity-50"
                                    >
                                        {isCancelling ? 'Cancelling...' : 'Confirm Cancel'}
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
};

const InfoBox: React.FC<{
    icon: any;
    label: string;
    value: string;
    color: string;
}> = ({ icon: Icon, label, value, color }) => (
    <div className="p-3 bg-white/5 rounded-xl border border-white/5">
        <div className="flex items-center gap-2 mb-1">
            <Icon className="w-3 h-3" style={{ color }} />
            <span className="text-[9px] text-gray-500 font-mono uppercase tracking-wider">
                {label}
            </span>
        </div>
        <p className="text-sm font-bold text-white font-mono">{value}</p>
    </div>
);

export default SubscriptionPanel;
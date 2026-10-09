import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    FiZap,
    FiX,
    FiArrowRight,
    FiAlertTriangle,
    FiClock,
    FiLock,
} from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';

import { GradientButton } from '../common/GradientButton';
import { useBillingStore } from '../../store/billingStore';
import { ROUTES } from '../../constants/routes';

const TRIGGER_CONFIG: Record<
    string,
    { title: string; message: string; icon: any; color: string }
> = {
    quota_warning: {
        title: 'Running Low on Searches',
        message:
            "You've used over 80% of your search quota. Upgrade to keep searching without interruption.",
        icon: FiAlertTriangle,
        color: '#facc15',
    },
    quota_exceeded: {
        title: 'Search Limit Reached',
        message:
            "You've hit your daily search limit. Upgrade to continue searching immediately.",
        icon: FiAlertTriangle,
        color: '#f87171',
    },
    feature_locked: {
        title: 'Premium Feature',
        message:
            'This feature is available on Pro tier and higher. Upgrade to unlock it.',
        icon: FiLock,
        color: '#a855f7',
    },
    trial_expired: {
        title: 'Trial Ended',
        message:
            'Your free trial has ended. Upgrade now to keep all premium features.',
        icon: FiClock,
        color: '#facc15',
    },
    usage_widget: {
        title: 'Unlock More Searches',
        message:
            'Get 100+ searches per day, all 12 platforms, and advanced features with Pro.',
        icon: FiZap,
        color: '#06b6d4',
    },
    default: {
        title: 'Upgrade Your Plan',
        message:
            'Unlock more searches, features, and platforms with a premium subscription.',
        icon: FiZap,
        color: '#06b6d4',
    },
};

export const UpgradePrompt: React.FC = () => {
    const navigate = useNavigate();
    const {
        isUpgradeModalOpen,
        upgradeModalTrigger,
        closeUpgradeModal,
    } = useBillingStore();

    const config = TRIGGER_CONFIG[upgradeModalTrigger || 'default'] || TRIGGER_CONFIG.default;
    const Icon = config.icon

    const handleUpgrade = () => {
        closeUpgradeModal();
        navigate(ROUTES.PRICING);
    };

    return (
        <AnimatePresence>
            {isUpgradeModalOpen && (
                <>
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={closeUpgradeModal}
                        className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-xl"
                    />

                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        transition={{ type: 'spring', damping: 25 }}
                        onClick={(e) => e.stopPropagation()}
                        className="fixed inset-0 z-[101] flex items-center justify-center p-4 pointer-events-none"
                    >
                        <div className="relative w-full max-w-md pointer-events-auto">
                            <div
                                className="absolute top-0 left-0 right-0 h-1 rounded-t-3xl"
                                style={{
                                    background: `linear-gradient(90deg, transparent, ${config.color}, transparent)`,
                                }}
                            />

                            <div className="bg-gray-950 border rounded-3xl overflow-hidden shadow-2xl"
                                style={{
                                    borderColor: `${config.color}30`,
                                    boxShadow: `0 25px 60px rgba(0,0,0,0.5), 0 0 40px ${config.color}15`,
                                }}
                            >
                                <button
                                    onClick={closeUpgradeModal}
                                    className="absolute top-4 right-4 z-10 p-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all"
                                >
                                    <FiX className="w-4 h-4 text-gray-400" />
                                </button>

                                <div className="p-6 sm:p-8 text-center">
                                    <motion.div
                                        initial={{ scale: 0, rotate: -180 }}
                                        animate={{ scale: 1, rotate: 0 }}
                                        transition={{ type: 'spring', stiffness: 200 }}
                                        className="w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center"
                                        style={{
                                            background: `linear-gradient(135deg, ${config.color}20, ${config.color}05)`,
                                            border: `1px solid ${config.color}30`,
                                        }}
                                    >
                                        <Icon className="w-8 h-8" style={{ color: config.color }} />
                                    </motion.div>

                                    <h2 className="text-xl font-bold text-white mb-2">
                                        {config.title}
                                    </h2>

                                    <p className="text-sm text-gray-400 mb-6 max-w-sm mx-auto leading-relaxed">
                                        {config.message}
                                    </p>

                                    <div className="p-4 bg-gradient-to-r from-cyan-500/10 to-purple-500/10 border border-cyan-500/20 rounded-xl text-left mb-6">
                                        <p className="text-[10px] font-mono font-semibold text-cyan-400 uppercase tracking-wider mb-2">
                                            Pro includes
                                        </p>
                                        <ul className="space-y-1.5 text-xs text-gray-300">
                                            <li className="flex items-center gap-2">
                                                <div className="w-1 h-1 rounded-full bg-cyan-400" />
                                                100 searches per day
                                            </li>
                                            <li className="flex items-center gap-2">
                                                <div className="w-1 h-1 rounded-full bg-cyan-400" />
                                                All 12 platforms
                                            </li>
                                            <li className="flex items-center gap-2">
                                                <div className="w-1 h-1 rounded-full bg-cyan-400" />
                                                Full 6-month history
                                            </li>
                                            <li className="flex items-center gap-2">
                                                <div className="w-1 h-1 rounded-full bg-cyan-400" />
                                                Voice recognition + analytics
                                            </li>
                                        </ul>
                                    </div>

                                    <div className="flex flex-col gap-2">
                                        <GradientButton
                                            onClick={handleUpgrade}
                                            variant="rainbow"
                                            size="lg"
                                            fullWidth
                                            pulse
                                            icon={<FiArrowRight />}
                                            iconPosition="right"
                                        >
                                            View Pricing & Upgrade
                                        </GradientButton>

                                        <button
                                            onClick={closeUpgradeModal}
                                            className="text-xs text-gray-500 hover:text-gray-300 font-mono transition-colors py-2"
                                        >
                                            Maybe later
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
};

export default UpgradePrompt;
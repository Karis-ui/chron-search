import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    FiZap,
    FiX,
    FiCheck,
    FiStar,
    FiAward,
    FiTrendingUp,
    FiChevronRight,
} from 'react-icons/fi';

import { GradientButton } from '../common/GradientButton';
import { useBilling } from '../../hooks/useBilling';
import { useBillingStore } from '../../store/billingStore';

const BOOST_PACKAGES = [
    {
        id: 'starter',
        name: 'Starter Boost',
        price: 4.99,
        duration: '7 days',
        boost: '+25%',
        color: '#06b6d4',
        icon: FiZap,
        features: ['+25% ranking boost', '7 days visibility', '~1,000 impressions'],
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
        features: ['+50% ranking boost', '30 days visibility', '~10,000 impressions'],
    },
    {
        id: 'premium',
        name: 'Premium Boost',
        price: 49.99,
        duration: '90 days',
        boost: '+100%',
        color: '#ec4899',
        icon: FiStar,
        features: ['+100% ranking boost', '90 days visibility', '~50,000 impressions'],
    },
];

const VERIFICATION_PACKAGES = [
    {
        id: 'blue',
        name: 'Verified',
        price: 9.99,
        color: '#06b6d4',
        icon: FiCheck,
        features: ['Blue checkmark', '+15% ranking', 'Cannot be impersonated'],
    },
    {
        id: 'purple',
        name: 'Premium Verified',
        price: 29.99,
        color: '#a855f7',
        icon: FiAward,
        popular: true,
        features: ['Purple checkmark', '+35% ranking', 'Featured in discover', 'Priority support'],
    },
    {
        id: 'gold',
        name: 'Elite',
        price: 99.99,
        color: '#eab308',
        icon: FiStar,
        features: ['Gold checkmark', '+75% ranking', 'Homepage feature', 'Custom profile URL', 'QR code'],
    },
];

export const PurchaseModal: React.FC = () => {
    const {
        isPurchaseModalOpen,
        closePurchaseModal,
        purchaseModalType,
    } = useBillingStore();

    const { buyBoost, isPurchasing, buyVerification } = useBilling();
    if (!purchaseModalType) return null;

    const isBoost = purchaseModalType === 'boost';
    const packages = isBoost ? BOOST_PACKAGES : VERIFICATION_PACKAGES;
    const title = isBoost ? "Boost Your Visibility" : "Verify Your Profile";
    const subtitle = isBoost ? 'Rank higher in search results' : 'Add a verification badge to your profile';

    const handlePurchase = (packageId: string) => {
        if (isBoost) {
            buyBoost(packageId);
        } else {
            buyVerification(packageId)
        }
    };
    return (
        <AnimatePresence>
            {isPurchaseModalOpen && (
                <>
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={closePurchaseModal}
                        className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-xl"
                    />

                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        transition={{ type: 'spring', damping: 25 }}
                        onClick={(e) => e.stopPropagation()}
                        className="fixed inset-0 z-[101] flex items-center justify-center p-4 pointer-events-none overflow-y-auto"
                    >
                        <div className="relative w-full max-w-3xl my-8 pointer-events-auto">
                            <div className="bg-gray-950 border border-white/10 rounded-3xl overflow-hidden shadow-2xl">
                                <button
                                    onClick={closePurchaseModal}
                                    className="absolute top-4 right-4 z-10 p-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all"
                                >
                                    <FiX className="w-4 h-4 text-gray-400" />
                                </button>

                                <div className="p-6 sm:p-8">
                                    <div className="text-center mb-8">
                                        <div
                                            className="w-14 h-14 mx-auto mb-4 rounded-2xl flex items-center justify-center"
                                            style={{
                                                background: isBoost
                                                    ? 'linear-gradient(135deg, #ec489920, #ec489905)'
                                                    : 'linear-gradient(135deg, #a855f720, #a855f705)',
                                                border: `1px solid ${isBoost ? '#ec4899' : '#a855f7'}30`,
                                            }}
                                        >
                                            {isBoost ? (
                                                <FiZap className="w-7 h-7 text-pink-400" />
                                            ) : (
                                                <FiAward className="w-7 h-7 text-purple-400" />
                                            )}
                                        </div>
                                        <h2 className="text-2xl font-bold text-white mb-2">{title}</h2>
                                        <p className="text-sm text-gray-400">{subtitle}</p>
                                    </div>

                                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                                        {packages.map((pkg) => {
                                            const Icon = pkg.icon;
                                            const isPopular = 'popular' in pkg && pkg.popular;

                                            return (
                                                <motion.div
                                                    key={pkg.id}
                                                    initial={{ opacity: 0, y: 20 }}
                                                    animate={{ opacity: 1, y: 0 }}
                                                    className={`relative p-5 rounded-2xl border-2 transition-all ${isPopular
                                                        ? 'border-purple-500/40 bg-gradient-to-b from-purple-500/5 to-transparent'
                                                        : 'border-white/10 bg-white/5 hover:border-white/20'
                                                        }`}
                                                >
                                                    {isPopular && (
                                                        <div className="absolute -top-2.5 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full text-[9px] font-bold text-white font-mono uppercase">
                                                            Popular
                                                        </div>
                                                    )}

                                                    <div
                                                        className="w-10 h-10 rounded-xl flex items-center justify-center mb-3"
                                                        style={{
                                                            background: `linear-gradient(135deg, ${pkg.color}20, ${pkg.color}05)`,
                                                            border: `1px solid ${pkg.color}30`,
                                                        }}
                                                    >
                                                        <Icon className="w-5 h-5" style={{ color: pkg.color }} />
                                                    </div>

                                                    <h3 className="text-base font-bold text-white mb-1">
                                                        {pkg.name}
                                                    </h3>

                                                    <div className="flex items-baseline gap-1 mb-3">
                                                        <span
                                                            className="text-2xl font-black font-mono"
                                                            style={{ color: pkg.color }}
                                                        >
                                                            ${pkg.price}
                                                        </span>
                                                        {'duration' in pkg && (
                                                            <span className="text-[10px] text-gray-500 font-mono">
                                                                /{String(pkg.duration)}
                                                            </span>
                                                        )}
                                                    </div>

                                                    {'boost' in pkg && (
                                                        <div className="mb-3">
                                                            <span
                                                                className="inline-block px-2 py-0.5 rounded-md text-[10px] font-mono font-bold"
                                                                style={{
                                                                    backgroundColor: `${pkg.color}20`,
                                                                    color: pkg.color,
                                                                }}
                                                            >
                                                                {String(pkg.boost)} ranking
                                                            </span>
                                                        </div>
                                                    )}

                                                    <ul className="space-y-1.5 mb-4">
                                                        {pkg.features.map((feature, i) => (
                                                            <li
                                                                key={i}
                                                                className="flex items-start gap-1.5 text-[11px] text-gray-400"
                                                            >
                                                                <FiCheck className="w-3 h-3 text-green-400 flex-shrink-0 mt-0.5" />
                                                                <span>{feature}</span>
                                                            </li>
                                                        ))}
                                                    </ul>

                                                    <GradientButton
                                                        onClick={() => handlePurchase(pkg.id)}
                                                        disabled={isPurchasing}
                                                        loading={isPurchasing}
                                                        variant={isPopular ? 'rainbow' : 'cyan'}
                                                        size="sm"
                                                        fullWidth
                                                        icon={<FiChevronRight />}
                                                        iconPosition="right"
                                                    >
                                                        Buy Now
                                                    </GradientButton>
                                                </motion.div>
                                            );
                                        })}
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

export default PurchaseModal;
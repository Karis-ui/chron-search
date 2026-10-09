import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    FiCheck,
    FiAlertCircle,
    FiLoader,
    FiCpu,
    FiArrowRight,
} from 'react-icons/fi';
import { toast } from 'react-hot-toast';

import { ParticleBackground } from '../common/ParticleBackground';
import { CyberGrid } from '../common/CyberGrid';
import { Scanline } from '../common/Scanline';
import { GradientButton } from '../common/GradientButton';
import { GlitchText } from '../common/GlitchText';
import { NeonBorder } from '../common/NeonBorder';
import { useBilling } from '../../hooks/useBilling';
import { ROUTES } from '../../constants/routes';

export const CheckoutRedirect: React.FC = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const { refresh } = useBilling();

    const sessionId = searchParams.get('session_id');
    const [displayStatus, setDisplayStatus] = useState<'processing' | 'success' | 'error'>(
        'processing'
    );

    useEffect(() => {
        const processReturn = async () => {
            await new Promise((r) => setTimeout(r, 1500));

            try {
                refresh();

                if (sessionId) {
                    setDisplayStatus('success');
                    toast.success('Payment successful!');
                } else {
                    setDisplayStatus('error');
                }
            } catch (error) {
                setDisplayStatus('error');
            }
        };

        processReturn();
    }, []);

    const handleContinue = () => {
        navigate(ROUTES.BILLING);
    };

    const config = {
        processing: {
            icon: FiLoader,
            color: '#06b6d4',
            title: 'PROCESSING',
            message: 'Confirming your payment...',
        },
        success: {
            icon: FiCheck,
            color: '#22c55e',
            title: 'PAYMENT SUCCESSFUL',
            message: 'Your plan is now active',
        },
        error: {
            icon: FiAlertCircle,
            color: '#f87171',
            title: 'SOMETHING WENT WRONG',
            message: 'Contact support if charged',
        },
    }[displayStatus];

    const Icon = config.icon;

    return (
        <div className="relative min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 overflow-hidden">
            <ParticleBackground />
            <CyberGrid animated speed={0.3} />
            <Scanline color={config.color} intensity={0.3} />

            <div className="relative z-10 max-w-md w-full">
                <NeonBorder
                    color={displayStatus === 'error' ? 'pink' : 'cyan'}
                    intensity="medium"
                >
                    <div className="p-8 text-center">
                        <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{ type: 'spring', stiffness: 200 }}
                            className="w-20 h-20 mx-auto mb-6 relative"
                        >
                            {displayStatus === 'processing' && (
                                <>
                                    <motion.div
                                        className="absolute inset-0 rounded-full"
                                        style={{ background: `linear-gradient(135deg, ${config.color}, ${config.color}80)` }}
                                        animate={{ rotate: 360 }}
                                        transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                                    />
                                    <div className="absolute inset-1 bg-gray-950 rounded-full flex items-center justify-center">
                                        <FiCpu className="w-8 h-8 text-cyan-400" />
                                    </div>
                                </>
                            )}

                            {displayStatus !== 'processing' && (
                                <div
                                    className="w-20 h-20 rounded-full flex items-center justify-center"
                                    style={{
                                        background: `${config.color}20`,
                                        border: `2px solid ${config.color}50`,
                                    }}
                                >
                                    <Icon className="w-10 h-10" style={{ color: config.color }} />
                                </div>
                            )}
                        </motion.div>

                        <h1 className="text-2xl font-bold text-white mb-3 font-mono">
                            <GlitchText glitchInterval={3000}>
                                {config.title}
                            </GlitchText>
                        </h1>

                        <p className="text-sm text-gray-400 font-mono mb-6">
                            {config.message}
                        </p>

                        {displayStatus === 'processing' && (
                            <div className="flex items-center justify-center gap-1.5 mb-6">
                                {[0, 1, 2, 3, 4].map((i) => (
                                    <motion.div
                                        key={i}
                                        className="w-2 h-2 rounded-full bg-cyan-400"
                                        animate={{ opacity: [0.2, 1, 0.2], scale: [1, 1.3, 1] }}
                                        transition={{
                                            duration: 1.2,
                                            repeat: Infinity,
                                            delay: i * 0.15,
                                        }}
                                    />
                                ))}
                            </div>
                        )}

                        {displayStatus === 'success' && (
                            <GradientButton
                                onClick={handleContinue}
                                variant="rainbow"
                                size="lg"
                                fullWidth
                                pulse
                                icon={<FiArrowRight />}
                                iconPosition="right"
                            >
                                Go to Billing
                            </GradientButton>
                        )}

                        {displayStatus === 'error' && (
                            <div className="space-y-3">
                                <GradientButton
                                    onClick={handleContinue}
                                    variant="cyan"
                                    size="lg"
                                    fullWidth
                                >
                                    Back to Billing
                                </GradientButton>
                                <button
                                    onClick={() => navigate(ROUTES.HOME)}
                                    className="text-xs text-gray-500 hover:text-gray-300 font-mono"
                                >
                                    Go Home
                                </button>
                            </div>
                        )}

                        {/* Status bar */}
                        <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-center gap-2 text-[10px] text-gray-600 font-mono">
                            <div
                                className="w-1.5 h-1.5 rounded-full animate-pulse"
                                style={{ backgroundColor: config.color }}
                            />
                            <span>{displayStatus.toUpperCase()}</span>
                        </div>
                    </div>
                </NeonBorder>
            </div>
        </div>
    );
};

export default CheckoutRedirect;
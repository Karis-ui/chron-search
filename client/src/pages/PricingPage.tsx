import React from 'react';
import { motion } from 'framer-motion';
import { FiArrowLeft, FiCpu } from 'react-icons/fi';
import { Link, useNavigate } from 'react-router-dom';

import { ParticleBackground } from '../components/common/ParticleBackground';
import { CyberGrid } from '../components/common/CyberGrid';
import { Scanline } from '../components/common/Scanline';
import { ROUTES } from '../constants/routes';
import { APP_CONFIG } from '../constants/config';
import { PricingTable } from '../components/billing/PricingTable';

export const PricingPage: React.FC = () => {
    const navigate = useNavigate();
    return (
        <div className="relative min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 py-8 px-4 overflow-x-hidden">
            <ParticleBackground />
            <CyberGrid animated speed={0.3} />
            <Scanline color="#06b6d4" intensity={0.3} />

            <motion.header
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="relative z-10 max-w-7xl mx-auto mb-8"
            >
                <div className="flex items-center justify-between">
                    <button
                        onClick={() => navigate(-1)}
                        className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all text-sm text-gray-300 hover:text-white font-mono group"
                    >
                        <FiArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
                        Back
                    </button>

                    <Link to={ROUTES.HOME} className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-purple-600 flex items-center justify-center shadow-lg shadow-purple-500/25">
                            <FiCpu className="w-5 h-5 text-white" />
                        </div>
                        <div className="text-right">
                            <p className="text-sm font-bold shimmer-text">{APP_CONFIG.name}</p>
                            <p className="text-[10px] text-gray-500 font-mono">
                                v{APP_CONFIG.version}
                            </p>
                        </div>
                    </Link>
                </div>
            </motion.header>

            <div className="relative z-10">
                <PricingTable />
            </div>

            <motion.footer
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="relative z-10 max-w-7xl mx-auto mt-16 text-center"
            >
                <div className="flex flex-wrap items-center justify-center gap-6 text-[10px] text-gray-500 font-mono">
                    <div className="flex items-center gap-1.5">
                        <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                        <span>Powered by Stripe</span>
                    </div>
                    <span className="text-gray-700">•</span>
                    <span>TLS 1.3</span>
                    <span className="text-gray-700">•</span>
                    <span>PCI DSS Compliant</span>
                </div>
            </motion.footer>
        </div>
    );
};

export default PricingPage;
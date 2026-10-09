import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { subscribeWithSelector } from 'zustand/middleware';

import type {
    SubscriptionSummary,
    UserCapabilities,
    TierInfo,
} from '../api/endpoints/billing';
import type { BalanceSummary } from '../api/endpoints/rewards';

interface BillingState {
    tiers: TierInfo[];
    subscription: SubscriptionSummary | null;
    capabilities: UserCapabilities | null;
    balance: BalanceSummary | null;

    isLoadingTiers: boolean;
    isLoadingSubscription: boolean;
    isLoadingCapabilities: boolean;
    isLoadingBalance: boolean;
    isCheckoutLoading: boolean;
    error: string | null;

    billingCycle: 'monthly' | 'yearly';
    isPurchaseModalOpen: boolean;
    purchaseModalType: 'boost' | 'verification' | null;
    isUpgradeModalOpen: boolean;
    upgradeModalTrigger: string | null;

    setTiers: (tiers: TierInfo[]) => void;
    setSubscription: (sub: SubscriptionSummary | null) => void;
    setCapabilities: (caps: UserCapabilities | null) => void;
    setBalance: (balance: BalanceSummary | null) => void;

    setLoading: (
        key:
            | 'isLoadingTiers'
            | 'isLoadingSubscription'
            | 'isLoadingCapabilities'
            | 'isLoadingBalance'
            | 'isCheckoutLoading',
        value: boolean
    ) => void;
    setError: (error: string | null) => void;

    setBillingCycle: (cycle: 'monthly' | 'yearly') => void;
    openPurchaseModal: (type: 'boost' | 'verification') => void;
    closePurchaseModal: () => void;
    openUpgradeModal: (trigger: string) => void;
    closeUpgradeModal: () => void;

    reset: () => void;
}

const initialState = {
    tiers: [],
    subscription: null,
    capabilities: null,
    balance: null,

    isLoadingTiers: false,
    isLoadingSubscription: false,
    isLoadingCapabilities: false,
    isLoadingBalance: false,
    isCheckoutLoading: false,

    error: null,

    billingCycle: 'monthly' as const,
    isPurchaseModalOpen: false,
    purchaseModalType: null,
    isUpgradeModalOpen: false,
    upgradeModalTrigger: null,
};

export const useBillingStore = create<BillingState>()(
    subscribeWithSelector(
        immer((set) => ({
            ...initialState,

            setTiers: (tiers) => {
                set((state) => {
                    state.tiers = tiers;
                });
            },
            setSubscription: (sub) => {
                set((state) => {
                    state.subscription = sub;
                });
            },
            setCapabilities: (caps) => {
                set((state) => {
                    state.capabilities = caps;
                });
            },
            setBalance: (balance) => {
                set((state) => {
                    state.balance = balance;
                });
            },
            setLoading: (key, value) => {
                set((state) => {
                    state[key] = value;
                });
            },
            setError: (error) => {
                set((state) => {
                    state.error = error;
                });
            },
            setBillingCycle: (cycle) => {
                set((state) => {
                    state.billingCycle = cycle;
                });
            },
            openPurchaseModal: (type) => {
                set((state) => {
                    state.isPurchaseModalOpen = true;
                    state.purchaseModalType = type;
                });
            },
            closePurchaseModal: () => {
                set((state) => {
                    state.isPurchaseModalOpen = false;
                    state.purchaseModalType = null;
                });
            },
            openUpgradeModal: (trigger) => {
                set((state) => {
                    state.isUpgradeModalOpen = true;
                    state.upgradeModalTrigger = trigger;
                });
            },
            closeUpgradeModal: () => {
                set((state) => {
                    state.isUpgradeModalOpen = false;
                    state.upgradeModalTrigger = null;
                });
            },
            reset: () => {
                set(initialState);
            },
        }))
    )
);
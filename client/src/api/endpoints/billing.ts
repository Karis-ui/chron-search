import apiClient from '../client';

export interface SubscriptionSummary {
    tier: string;
    tier_name: string;
    status: string;
    billing_cycle: string;

    current_period_start?: string;
    current_period_end?: string;
    cancel_at_period_end: boolean;

    amount: number;
    currency: string;

    is_active: boolean;
    in_trial: boolean;
    trial_end?: string;

    limits: {
        searches_per_day: number;
        searches_per_month: number;
        results_per_search: number;
        time_range_days: number;
        platforms_count: number | 'all';
        export_formats: string[];
        saved_searches: number;
        api_calls_per_month: number;
        boosts_per_month: number;
        history_retention_days: number;
    };

    features: {
        voice_recognition: boolean;
        batch_search: boolean;
        advanced_filters: boolean;
        alerts_enabled: boolean;
        priority_support: boolean;
        analytics_access: boolean;
    };

    created_at?: string;
}

export interface TierInfo {
    id: string;
    name: string;
    description: string;
    price_monthly: number;
    price_yearly: number;
    limits: Record<string, any>;
}

export interface UserCapabilities {
    tier: string;
    tier_name: string;
    limits: Record<string, any>;
    features: Record<string, boolean>;
    usage: {
        searches_today: number;
        searches_this_month: number;
        api_calls_this_month: number;
        daily_remaining: number;
        monthly_remaining: number;
    };
    rewards: {
        multiplier: number;
        monthly_cap: number;
    };
}

export interface PaymentHistoryItem {
    id: string;
    amount: number;
    currency: string;
    status: string;
    type: string;
    description?: string;
    created_at: string;
}

export interface SubscriptionStats {
    tier: string;
    status: string;
    member_since?: string;
    total_payments: number;
    total_spent: number;
    recent_payments: PaymentHistoryItem[];
}

export type CheckoutType = 'subscription' | 'boost' | 'verification';

export interface CheckoutRequest {
    tier?: string;
    billing_cycle?: 'monthly' | 'yearly';
    boost_type?: 'starter' | 'staandard' | 'premium' | 'employer';
    level?: 'blue' | 'purple' | 'gold'
}

export const billingApi = {
    getTiers: async (): Promise<TierInfo[]> => {
        return apiClient.get<TierInfo[]>('/api/v1/subscriptions/tiers');
    },

    getMySubscription: async (): Promise<SubscriptionSummary> => {
        return apiClient.get<SubscriptionSummary>('/api/v1/subscriptions/me');
    },

    getCapabilities: async (): Promise<UserCapabilities> => {
        return apiClient.get<UserCapabilities>('/api/v1/subscriptions/capabilities');
    },

    checkTrialEligibility: async (): Promise<{ eligible: boolean }> => {
        return apiClient.get<{ eligible: boolean }>('/api/v1/subscriptions/trial/eligible');
    },

    getUpgradeOptions: async (): Promise<TierInfo[]> => {
        return apiClient.get<TierInfo[]>('/api/v1/subscriptions/upgrade-options');
    },

    getStats: async (): Promise<SubscriptionStats> => {
        return apiClient.get<SubscriptionStats>('/api/v1/subscriptions/stats');
    },

    startSubscriptionCheckout: async (
        tier: string,
        billingCycle: 'monthly' | 'yearly' = 'monthly'
    ): Promise<{ checkout_url: string }> => {
        return apiClient.post('/api/v1/billing/checkout/subscription', {
            tier,
            billing_cycle: billingCycle,
        });
    },

    startBoostCheckout: async (
        boostType: string
    ): Promise<{ checkout_url: string }> => {
        return apiClient.post('/api/v1/billing/checkout/boost', {
            boost_type: boostType,
        });
    },

    startVerificationCheckout: async (
        level: string
    ): Promise<{ checkout_url: string }> => {
        return apiClient.post('/api/v1/billing/checkout/verification', {
            level,
        });
    },

    openCustomerPortal: async (): Promise<{ portal_url: string }> => {
        return apiClient.post('/api/v1/billing/portal');
    },

    cancelSubscription: async (immediate = false): Promise<{ message: string }> => {
        return apiClient.post(`/api/v1/billing/subscription/cancel?immediate=${immediate}`);
    },

    resumeSubscription: async (): Promise<{ message: string }> => {
        return apiClient.post('/api/v1/billing/subscription/resume');
    },

    getPayments: async (limit = 50): Promise<PaymentHistoryItem[]> => {
        return apiClient.get<PaymentHistoryItem[]>(
            `/api/v1/billing/payments?limit=${limit}`
        );
    },
};

export default billingApi;
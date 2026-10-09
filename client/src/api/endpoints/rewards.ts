import apiClient from '../client';


export interface BalanceSummary {
    available: number;
    pending: number;
    lifetime_earned: number;
    lifetime_paid: number;
    lifetime_searches: number;
    monthly_earned: number;
    monthly_cap: number;
    minimum_payout: number;
    can_withdraw: boolean;
    stripe_onboarding_complete: boolean;
    stripe_account_status?: string;
}

export interface LedgerEntry {
    id: string;
    amount: number;
    type: string;
    description?: string;
    status: 'pending' | 'confirmed' | 'paid' | 'failed';
    created_at: string;
}

export interface LedgerResponse {
    total: number;
    entries: LedgerEntry[];
}

export interface EarningsBreakdown {
    breakdown: Record<
        string,
        {
            count: number;
            total: number;
        }
    >;
    daily: Array<{
        date: string;
        amount: number;
    }>;
}

export interface PayoutRecord {
    id: string;
    amount: number;
    currency: string;
    status: 'pending' | 'processing' | 'paid' | 'failed';
    payout_method: string;
    requested_at: string;
    completed_at?: string;
    failure_reason?: string;
}

export interface ConnectStatus {
    has_account: boolean;
    account_id?: string;
    account_status?: string;
    onboarding_complete: boolean;
    can_receive_payouts: boolean;
}

export const rewardsApi = {
    getBalance: async (): Promise<BalanceSummary> => {
        return apiClient.get('/api/v1/rewards/balance')
    },
    getLedger: async (limit = 50, offset = 0): Promise<LedgerResponse> => {
        return apiClient.get(`/api/v1/rewards/ledger?limit=${limit}&offset=${offset}`)
    },
    getEarnings: async (): Promise<EarningsBreakdown> => {
        return apiClient.get('/api/v1/rewards/earnings')
    },
    getRecentPayouts: async (limit = 50): Promise<PayoutRecord[]> => {
        return apiClient.get(`/api/v1/rewards/payouts?limit=${limit}`)
    },
    confirmPendingPayout: async (): Promise<{ confirmed: number; count: number }> => {
        return apiClient.post('/api/v1/rewards/confirm-pending')
    },
    getConnectStatus: async (): Promise<ConnectStatus> => {
        return apiClient.get('/api/v1/rewards/connect/status')
    },
    startConnectOnboarding: async (): Promise<{ onboarding_url: string }> => {
        return apiClient.post('/api/v1/rewards/connect/onboarding')
    },
    requestPayout: async (amount?: number): Promise<PayoutRecord> => {
        return apiClient.post('/api/v1/rewards/payouts', { amount })
    },
    getPayouts: async (limit = 50): Promise<PayoutRecord[]> => {
        return apiClient.get(`/api/v1/rewards/payouts?limit=${limit}`)
    }
};

export default rewardsApi;
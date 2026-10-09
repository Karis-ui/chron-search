import { useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';

import {
    billingApi
} from '../api/endpoints/billing';
import rewardsApi from '../api/endpoints/rewards';
import { useBillingStore } from '../store/billingStore';
import { useAuthStore } from '../store/authStore';

export const useBilling = () => {
    const queryClient = useQueryClient();
    const { accessToken } = useAuthStore();
    const isAuthenticated = !!accessToken;
    const {
        tiers,
        subscription,
        capabilities,
        balance,
        error,
        billingCycle,
        setSubscription,
        setCapabilities,
        setBalance,
        setLoading,
        setError,
        setBillingCycle,
        openPurchaseModal,
        closePurchaseModal,
        openUpgradeModal,
        closeUpgradeModal,
    } = useBillingStore();

    const tiersQuery = useQuery({
        queryKey: ['billing', 'tiers'],
        queryFn: billingApi.getTiers,
        staleTime: 1000 * 60 * 60,
    });

    const subscriptionQuery = useQuery({
        queryKey: ['billing', 'subscription'],
        queryFn: billingApi.getMySubscription,
        staleTime: 1000 * 60 * 60,
        enabled: isAuthenticated,
    });

    const capabilitiesQuery = useQuery({
        queryKey: ['billing', 'capabilities'],
        queryFn: billingApi.getCapabilities,
        staleTime: 1000 * 60 * 60,
        enabled: isAuthenticated,
    });

    const balanceQuery = useQuery({
        queryKey: ['billing', 'balance'],
        queryFn: rewardsApi.getBalance,
        staleTime: 1000 * 60 * 60,
        enabled: isAuthenticated,
    });

    const subscribeMutation = useMutation({
        mutationFn: ({ tier, cycle }: { tier: string; cycle: 'monthly' | 'yearly' }) => billingApi.startSubscriptionCheckout(tier, cycle),
        onSuccess: (data) => {
            window.location.href = data.checkout_url;
        },

        onError: (err: any) => {
            const msg = err?.response?.data?.detail || 'Checkout failed';
            toast.error(msg);
        },
    });

    const boostMutation = useMutation({
        mutationFn: (boostType: string) => billingApi.startBoostCheckout(boostType),
        onSuccess: (data) => {
            window.location.href = data.checkout_url;
        },

        onError: (err: any) => {
            const msg = err?.response?.data?.detail || 'Checkout failed';
            toast.error(msg);
        },
    });

    const verificationMutation = useMutation({
        mutationFn: (verificationType: string) => billingApi.startVerificationCheckout(verificationType),
        onSuccess: (data) => {
            window.location.href = data.checkout_url;
        },
        onError: (err: any) => {
            const msg = err?.response?.data?.detail || 'Checkout failed';
            toast.error(msg);
        },
    });

    const connectMutation = useMutation({
        mutationFn: rewardsApi.startConnectOnboarding,
        onSuccess: (data) => {
            window.location.href = data.onboarding_url;
        },
        onError: (err: any) => {
            const msg = err?.response?.data?.detail || 'Failed to start onboarding';
            toast.error(msg);
        },
    });

    const resumeMutation = useMutation({
        mutationFn: billingApi.resumeSubscription,
        onSuccess: () => {
            toast.success('Subscription resumed');
            queryClient.invalidateQueries({ queryKey: ['billing'] });
        },
        onError: (err: any) => {
            const msg = err?.response?.data?.detail || 'Failed to resume subscription';
            toast.error(msg);
        },
    });

    const cancelMutation = useMutation({
        mutationFn: (immediate: boolean) => billingApi.cancelSubscription(immediate),
        onSuccess: () => {
            toast.success('Subscription will end at period end');
            queryClient.invalidateQueries({ queryKey: ['billing'] });
        },
        onError: (err: any) => {
            const msg = err?.response?.data?.detail || 'Failed to cancel subscription';
            toast.error(msg);
        },
    });

    const payoutMutation = useMutation({
        mutationFn: (amount?: number) => rewardsApi.requestPayout(amount),
        onSuccess: () => {
            toast.success('Payout initiated');
            queryClient.invalidateQueries({ queryKey: ['billing', 'balance'] });
        },
        onError: (err: any) => {
            const msg = err?.response?.data?.detail || 'Failed to request payout';
            toast.error(msg);
        },
    });

    const portalMutation = useMutation({
        mutationFn: billingApi.openCustomerPortal,
        onSuccess: (data) => {
            window.location.href = data.portal_url;
        },
        onError: (err: any) => {
            const msg = err?.response?.data?.detail || 'Failed to start portal session';
            toast.error(msg);
        },
    });

    useEffect(() => {
        if (error) {
            toast.error(error);
            setError(null);
        }
    }, [error, setError]);

    useEffect(() => {
        if (isAuthenticated && !subscriptionQuery.isLoading) {
            setLoading('isLoadingSubscription', subscriptionQuery.isLoading);

            if (subscriptionQuery.data) {
                setSubscription(subscriptionQuery.data);
            }

            if (capabilitiesQuery.data) {
                setCapabilities(capabilitiesQuery.data);
            }

            if (balanceQuery.data) {
                setBalance(balanceQuery.data);
            }

            setLoading('isLoadingTiers', false);
            setLoading('isLoadingCapabilities', false);
            setLoading('isLoadingBalance', false);
            setLoading('isCheckoutLoading', false);
        }

    }, [isAuthenticated, subscriptionQuery, capabilitiesQuery, balanceQuery]);

    const hasFeature = useCallback(
        (feature: string): boolean => {
            if (!capabilities) return false;
            return !!capabilities.features[feature];
        },
        [capabilities]
    );

    const isTierAtLeast = useCallback(
        (tier: string): boolean => {
            const order = ['free', 'pro', 'ultra', 'enterprise'];
            const current = capabilities?.tier || 'free';
            return order.indexOf(current) >= order.indexOf(tier);
        },
        [capabilities]
    );

    const hasSearchesRemaining = useCallback((): boolean => {
        if (!capabilities) return true;
        const { daily_remaining, monthly_remaining } = capabilities.usage;
        if (daily_remaining === -1) return true; // unlimited
        return daily_remaining > 0 && (monthly_remaining === -1 || monthly_remaining > 0);
    }, [capabilities]);

    const getSearchesRemaining = useCallback((): string => {
        if (!capabilities) return '';
        const { daily_remaining } = capabilities.usage;
        if (daily_remaining === -1) return 'Unlimited';
        return `${daily_remaining} remaining today`;
    }, [capabilities]);

    useEffect(() => {
        if (isAuthenticated && !capabilitiesQuery.isSuccess) {
            capabilitiesQuery.refetch();
        }
    }, [isAuthenticated]);

    return {
        tiers,
        subscription,
        capabilities,
        balance,
        billingCycle,
        isLoading:
            tiersQuery.isLoading ||
            subscriptionQuery.isLoading ||
            capabilitiesQuery.isLoading ||
            balanceQuery.isLoading,
        isSubscribing: subscribeMutation.isPending,
        isPurchasing:
            boostMutation.isPending || verificationMutation.isPending,
        isCancelling: cancelMutation.isPending,
        isResuming: resumeMutation.isPending,
        isRequestingPayout: payoutMutation.isPending,
        isConnectingStripe: connectMutation.isPending,

        subscribe: (tier: string, cycle: 'monthly' | 'yearly' = 'monthly') =>
            subscribeMutation.mutate({ tier, cycle }),
        buyBoost: (boostType: string) => boostMutation.mutate(boostType),
        buyVerification: (level: string) => verificationMutation.mutate(level),
        openPortal: () => portalMutation.mutate(),
        cancelSubscription: (immediate = false) => cancelMutation.mutate(immediate),
        resumeSubscription: () => resumeMutation.mutate(),
        requestPayout: (amount?: number) => payoutMutation.mutate(amount),
        startConnect: () => connectMutation.mutate(),

        hasFeature,
        isTierAtLeast,
        hasSearchesRemaining,
        getSearchesRemaining,

        openPurchaseModal,
        closePurchaseModal,
        openUpgradeModal,
        closeUpgradeModal,
        setBillingCycle,

        refresh: () => {
            subscriptionQuery.refetch();
            capabilitiesQuery.refetch();
            balanceQuery.refetch();
        },
    };
};
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

class Tier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ULTRA = "ultra"
    ENTERPRISE = "enterprise"

@dataclass
class TierLimits:

    searches_per_day: int          
    searches_per_month: int       
    results_per_search: int
    concurrent_searches: int

    time_range_days: int           
    platforms_allowed: List[str]    
    export_formats: List[str]      
    voice_recognition: bool
    batch_search: bool             
    advanced_filters: bool
    saved_searches: int            
    alerts_enabled: bool
    api_calls_per_month: int

    profile_boosts_per_month: int
    verification_discount: float   
    priority_support: bool
    analytics_access: bool
    history_retention_days: int

    reward_multiplier: float       
    monthly_reward_cap: float

    name: str = ""
    description: str = ""
    price_monthly: float = 0
    price_yearly: float = 0


TIER_LIMITS: Dict[Tier, TierLimits] = {

    Tier.FREE: TierLimits(
        searches_per_day=3,
        searches_per_month=50,
        results_per_search=5,
        concurrent_searches=1,

        time_range_days=30,              
        platforms_allowed=["instagram", "twitter", "reddit"],  
        export_formats=[],              
        voice_recognition=False,
        batch_search=False,
        advanced_filters=False,
        saved_searches=0,
        alerts_enabled=False,
        api_calls_per_month=0,

        profile_boosts_per_month=0,
        verification_discount=0.0,
        priority_support=False,
        analytics_access=False,
        history_retention_days=7,

        reward_multiplier=1.0,
        monthly_reward_cap=20.0,

        name="Explorer",
        description="Perfect for trying out Chronos",
        price_monthly=0,
        price_yearly=0,
    ),

    Tier.PRO: TierLimits(
        searches_per_day=100,
        searches_per_month=2000,
        results_per_search=100,
        concurrent_searches=3,

        time_range_days=180,               
        platforms_allowed=[],             
        export_formats=["json", "csv"],
        voice_recognition=True,
        batch_search=False,
        advanced_filters=True,
        saved_searches=50,
        alerts_enabled=True,
        api_calls_per_month=1000,

        profile_boosts_per_month=3, 
        verification_discount=0.10,         
        priority_support=True,
        analytics_access=True,
        history_retention_days=90,

        reward_multiplier=1.5,           
        monthly_reward_cap=200.0,

        name="Professional",
        description="For serious investigators",
        price_monthly=29.00,
        price_yearly=290.00,
    ),

    Tier.ULTRA: TierLimits(
        searches_per_day=1000,
        searches_per_month=20000,
        results_per_search=500,
        concurrent_searches=10,

        time_range_days=180,
        platforms_allowed=[],              
        export_formats=["json", "csv", "pdf", "xlsx"],
        voice_recognition=True,
        batch_search=True,                 
        advanced_filters=True,
        saved_searches=500,
        alerts_enabled=True,
        api_calls_per_month=10000,

        profile_boosts_per_month=20,
        verification_discount=0.25,         
        priority_support=True,
        analytics_access=True,
        history_retention_days=180,

        reward_multiplier=2.0,
        monthly_reward_cap=500.0,

        name="Ultra",
        description="For power users and teams",
        price_monthly=99.00,
        price_yearly=990.00,
    ),

    Tier.ENTERPRISE: TierLimits(
        searches_per_day=-1,               
        searches_per_month=-1,
        results_per_search=-1,
        concurrent_searches=100,
        time_range_days=180,
        platforms_allowed=[],
        export_formats=["json", "csv", "pdf", "xlsx", "s3"],
        voice_recognition=True,
        batch_search=True,
        advanced_filters=True,
        saved_searches=-1,
        alerts_enabled=True,
        api_calls_per_month=-1,          

        profile_boosts_per_month=-1,
        verification_discount=0.50, 
        priority_support=True,
        analytics_access=True,
        history_retention_days=365,

        reward_multiplier=3.0,
        monthly_reward_cap=2000.0,

        name="Enterprise",
        description="Custom pricing for organizations",
        price_monthly=0,                  
        price_yearly=0,
    ),
}

def get_tier_limits(tier: str) -> TierLimits:
    if isinstance(tier, str):
        tier = Tier(tier.lower())
    return TIER_LIMITS[tier]


def is_tier_at_least(user_tier: str, required_tier: str) -> bool:
    order = [Tier.FREE, Tier.PRO, Tier.ULTRA, Tier.ENTERPRISE]
    try:
        user_idx = order.index(Tier(user_tier.lower()))
        required_idx = order.index(Tier(required_tier.lower()))
        return user_idx >= required_idx
    except (ValueError, AttributeError):
        return False


def get_tier_order() -> List[str]:
    return [t.value for t in [Tier.FREE, Tier.PRO, Tier.ULTRA, Tier.ENTERPRISE]]


def compare_tiers(tier1: str, tier2: str) -> int:
    order = [Tier.FREE, Tier.PRO, Tier.ULTRA, Tier.ENTERPRISE]
    try:
        i1 = order.index(Tier(tier1.lower()))
        i2 = order.index(Tier(tier2.lower()))
        return (i1 > i2) - (i1 < i2)
    except (ValueError, AttributeError):
        return 0


def get_all_tier_info() -> List[Dict[str, Any]]:
    tiers = []
    for tier in [Tier.FREE, Tier.PRO, Tier.ULTRA, Tier.ENTERPRISE]:
        limits = TIER_LIMITS[tier]
        tiers.append({
            "id": tier.value,
            "name": limits.name,
            "description": limits.description,
            "price_monthly": limits.price_monthly,
            "price_yearly": limits.price_yearly,
            "limits": {
                "searches_per_day": limits.searches_per_day,
                "searches_per_month": limits.searches_per_month,
                "results_per_search": limits.results_per_search,
                "time_range_days": limits.time_range_days,
                "platforms_count": len(limits.platforms_allowed) if limits.platforms_allowed else "all",
                "export_formats": limits.export_formats,
                "voice_recognition": limits.voice_recognition,
                "batch_search": limits.batch_search,
                "advanced_filters": limits.advanced_filters,
                "saved_searches": limits.saved_searches,
                "alerts_enabled": limits.alerts_enabled,
                "api_calls_per_month": limits.api_calls_per_month,
                "priority_support": limits.priority_support,
                "analytics_access": limits.analytics_access,
                "history_retention_days": limits.history_retention_days,
                "profile_boosts_per_month": limits.profile_boosts_per_month,
                "verification_discount": limits.verification_discount,
                "reward_multiplier": limits.reward_multiplier,
                "monthly_reward_cap": limits.monthly_reward_cap,
            },
        })
    return tiers
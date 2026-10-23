"""
ranked.py — Sub Ladder v6.0+
ELO rating system and ranked matchmaking.

Rank system (best to worst):
- Grand Champion: Top 500 players globally
- Champion: 2400+ ELO
- Diamond I/II/III: 2100-2399 ELO
- Ruby I/II/III: 1800-2099 ELO
- Emerald I/II/III: 1500-1799 ELO
- Platinum I/II/III: 1200-1499 ELO
- Gold I/II/III: 1000-1199 ELO
- Silver I/II/III: 800-999 ELO
- Bronze I/II/III: 600-799 ELO
- Iron I/II/III: 0-599 ELO
"""

from typing import Tuple, Dict, List, Optional
from enum import Enum

# ══════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════

DEFAULT_ELO = 1000
K_FACTOR = 32  # standard ELO K-factor
K_FACTOR_HIGH = 16  # reduced K-factor for high ELO (2400+)

# ══════════════════════════════════════════════════════════════════
# RANK DEFINITIONS
# ══════════════════════════════════════════════════════════════════

class RankTier(Enum):
    IRON = "Iron"
    BRONZE = "Bronze"
    SILVER = "Silver"
    GOLD = "Gold"
    PLATINUM = "Platinum"
    EMERALD = "Emerald"
    RUBY = "Ruby"
    DIAMOND = "Diamond"
    CHAMPION = "Champion"
    GRAND_CHAMPION = "Grand Champion"

class RankDivision(Enum):
    I = 1
    II = 2
    III = 3

# Tier boundaries (min ELO to reach tier)
TIER_BOUNDARIES = {
    RankTier.GRAND_CHAMPION: 2500,  # Top 500 only
    RankTier.CHAMPION: 2400,
    RankTier.DIAMOND: 2100,
    RankTier.RUBY: 1800,
    RankTier.EMERALD: 1500,
    RankTier.PLATINUM: 1200,
    RankTier.GOLD: 1000,
    RankTier.SILVER: 800,
    RankTier.BRONZE: 600,
    RankTier.IRON: 0,
}

# Division boundaries (min ELO within tier)
DIVISION_RANGES = {
    1: {"min": 0, "max": 99},      # Division I (bottom)
    2: {"min": 100, "max": 199},   # Division II (middle)
    3: {"min": 200, "max": 299},   # Division III (top)
}

# ══════════════════════════════════════════════════════════════════
# ELO CALCULATION
# ══════════════════════════════════════════════════════════════════

def expected_score(rating_a: int, rating_b: int) -> float:
    """Calculate expected win probability for player A."""
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

def calculate_k_factor(elo: int) -> int:
    """Return K-factor based on ELO (higher ELO = lower K-factor)."""
    if elo >= 2400:
        return K_FACTOR_HIGH
    return K_FACTOR

def new_ratings(winner_elo: int, loser_elo: int) -> Tuple[int, int]:
    """
    Calculate new ELO ratings after a match.
    Returns (new_winner_elo, new_loser_elo).
    """
    k_w = calculate_k_factor(winner_elo)
    k_l = calculate_k_factor(loser_elo)
    
    exp_w = expected_score(winner_elo, loser_elo)
    exp_l = expected_score(loser_elo, winner_elo)
    
    return (
        round(winner_elo + k_w * (1 - exp_w)),
        round(loser_elo + k_l * (0 - exp_l)),
    )

# ══════════════════════════════════════════════════════════════════
# RANK DETERMINATION
# ══════════════════════════════════════════════════════════════════

def get_tier_from_elo(elo: int) -> RankTier:
    """Get the rank tier for a given ELO rating."""
    for tier, min_elo in sorted(TIER_BOUNDARIES.items(), 
                                  key=lambda x: x[1], reverse=True):
        if elo >= min_elo:
            return tier
    return RankTier.IRON

def get_division_in_tier(elo: int, tier: RankTier) -> Optional[int]:
    """Get division (1, 2, or 3) within a tier. Champion and Grand Champion have no divisions."""
    if tier in (RankTier.CHAMPION, RankTier.GRAND_CHAMPION):
        return None

    tier_min = TIER_BOUNDARIES[tier]
    tier_offset = elo - tier_min

    if tier_offset >= 200:
        return 3
    elif tier_offset >= 100:
        return 2
    else:
        return 1

def get_rank_display(elo: int) -> Dict[str, any]:
    """
    Get complete rank information for a player.
    Returns dict with tier, division, and display string.
    """
    tier = get_tier_from_elo(elo)

    if tier in (RankTier.CHAMPION, RankTier.GRAND_CHAMPION):
        display_name = "Champion" if tier == RankTier.CHAMPION else "Grand Champion"
        return {
            "tier": tier.value,
            "division": None,
            "elo": elo,
            "display": display_name,
            "icon": "champion" if tier == RankTier.CHAMPION else "gc",
        }

    division = get_division_in_tier(elo, tier)

    return {
        "tier": tier.value,
        "division": division,
        "elo": elo,
        "display": f"{tier.value} {RankDivision(division).name}",
        "icon": f"{tier.name.lower()}_{division}",
    }

# ══════════════════════════════════════════════════════════════════
# LEADERBOARD & STATS
# ══════════════════════════════════════════════════════════════════

def rank_order() -> List[str]:
    """Return ordered list of ranks from best to worst."""
    return [
        "Grand Champion",
        "Champion",
        "Diamond III", "Diamond II", "Diamond I",
        "Ruby III", "Ruby II", "Ruby I",
        "Emerald III", "Emerald II", "Emerald I",
        "Platinum III", "Platinum II", "Platinum I",
        "Gold III", "Gold II", "Gold I",
        "Silver III", "Silver II", "Silver I",
        "Bronze III", "Bronze II", "Bronze I",
        "Iron III", "Iron II", "Iron I",
    ]

def get_progression_to_next_rank(elo: int) -> Dict[str, any]:
    """
    Get information about progression to the next rank/division.
    """
    current_tier = get_tier_from_elo(elo)

    if current_tier == RankTier.GRAND_CHAMPION:
        return {
            "current": "Grand Champion",
            "next": None,
            "current_elo": elo,
            "elo_to_next": None,
            "progress_percent": 100,
        }

    if current_tier == RankTier.CHAMPION:
        next_tier_elo = 2500
        return {
            "current": "Champion",
            "next": "Grand Champion",
            "current_elo": elo,
            "elo_to_next": next_tier_elo - elo,
            "progress_percent": min(100, max(0, ((elo - 2400) / 100) * 100)),
        }

    current_division = get_division_in_tier(elo, current_tier)
    tier_min = TIER_BOUNDARIES[current_tier]
    tier_offset = elo - tier_min

    if current_division is not None and current_division < 3:
        # Progress to next division
        next_div = current_division + 1
        div_progress = (tier_offset % 100)
        next_tier_elo = tier_min + (next_div * 100)

        return {
            "current": f"{current_tier.value} {current_division}",
            "next": f"{current_tier.value} {next_div}",
            "current_elo": elo,
            "elo_to_next": next_tier_elo - elo,
            "progress_percent": (div_progress / 100) * 100,
        }
    else:
        # Progress to next tier
        tier_list = list(TIER_BOUNDARIES.keys())
        current_idx = tier_list.index(current_tier)

        if current_idx == 0:
            return {
                "current": "Grand Champion",
                "next": None,
                "current_elo": elo,
                "elo_to_next": None,
                "progress_percent": 100,
            }

        next_tier = tier_list[current_idx - 1]
        next_tier_elo = TIER_BOUNDARIES[next_tier]

        return {
            "current": f"{current_tier.value} III",
            "next": f"{next_tier.value} I",
            "current_elo": elo,
            "elo_to_next": next_tier_elo - elo,
            "progress_percent": ((elo - tier_min) / 300) * 100,
        }

# ══════════════════════════════════════════════════════════════════
# MATCHMAKING
# ══════════════════════════════════════════════════════════════════

MATCHMAKING_ELO_RANGE = 200  # Find opponents within ±200 ELO

def is_valid_opponent(player_elo: int, opponent_elo: int) -> bool:
    """Check if two players are within acceptable ELO range for ranked match."""
    return abs(player_elo - opponent_elo) <= MATCHMAKING_ELO_RANGE

# ══════════════════════════════════════════════════════════════════
# DECAY SYSTEM (Champions & Grand Champions)
# ══════════════════════════════════════════════════════════════════

def is_subject_to_decay(elo: int) -> bool:
    """Check if a player is subject to decay (Champion or higher)."""
    return elo >= 2400

def decay_days_needed(elo: int) -> int:
    """
    Return the decay days a player should have when reaching a rank.
    """
    if elo >= 2400:
        return 21  # New Champion/Grand Champion gets 21 days
    return 0

# ══════════════════════════════════════════════════════════════════
# LEGACY COMPATIBILITY
# ══════════════════════════════════════════════════════════════════

def elo_rank(elo: int) -> str:
    """
    Legacy function for backward compatibility.
    Returns simple tier string.
    """
    return get_tier_from_elo(elo).value

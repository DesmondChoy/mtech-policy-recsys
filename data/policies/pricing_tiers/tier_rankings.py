"""
Pricing Tier Ranking Data

This module stores the relative price ranking of policy tiers for each insurer.
The ranking is used in the insurer-level policy comparison script to break ties
when multiple tiers are equally suitable based on coverage requirements.

The lists are ordered from cheapest tier to most expensive tier.
"""

INSURER_TIER_RANKING = {
    "fwd": ["Premium", "Business", "First"],  # Cheapest to Most Expensive
    "income": ["Classic", "Deluxe", "Preferred"],
    "sompo": ["Vital", "Deluxe", "GO Japan!", "Elite"],
    "gels": ["Basic", "Gold", "Platinum"],
}


# Helper function to easily access the ranking data
def get_insurer_tier_ranking():
    """Returns the dictionary containing insurer tier rankings."""
    return INSURER_TIER_RANKING

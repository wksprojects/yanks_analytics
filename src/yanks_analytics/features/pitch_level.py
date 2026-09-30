"""Pitch classification shared by the hitter tables in ``season.py``.

Flags each Statcast pitch as in or out of the zone, swing or take, whiff or
contact, and assigns a pitch group (fastball, breaking, offspeed, other).
"""

import pandas as pd


# Pitch type groupings (Statcast pitch_type codes)
PITCH_GROUPS = {
    "fastball": ["FF", "SI", "FC"],  # 4-seam, sinker, cutter
    # slider, sweeper, curve, knuckle-curve, slurve, slow curve
    "breaking": ["SL", "ST", "CU", "KC", "SV", "CS"],
    "offspeed": ["CH", "FS", "FO", "SC"],  # changeup, splitter, forkball, screwball
}


SWING_DESCRIPTIONS = frozenset([
    "swinging_strike", "swinging_strike_blocked",
    "foul", "foul_tip", "foul_bunt",
    "hit_into_play", "hit_into_play_score", "hit_into_play_no_out",
])

WHIFF_DESCRIPTIONS = frozenset(["swinging_strike", "swinging_strike_blocked"])


def classify_pitches(bp: pd.DataFrame) -> pd.DataFrame:
    """Add in_zone, is_swing, is_whiff columns using vectorized operations."""
    bp = bp.copy()
    zone_known = bp[["plate_x", "plate_z", "sz_bot", "sz_top"]].notna().all(axis=1)
    bp["zone_known"] = zone_known
    bp["in_zone"] = (
        bp["plate_x"].between(-0.83, 0.83)
        & bp["plate_z"].between(bp["sz_bot"], bp["sz_top"])
        & zone_known
    )
    bp["is_swing"] = bp["description"].isin(SWING_DESCRIPTIONS)
    bp["is_whiff"] = bp["description"].isin(WHIFF_DESCRIPTIONS)
    bp["pitch_group"] = bp["pitch_type"].map(
        {code: group for group, codes in PITCH_GROUPS.items() for code in codes}
    ).fillna("other")
    return bp

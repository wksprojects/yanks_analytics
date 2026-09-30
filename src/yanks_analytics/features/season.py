"""Hitter tables from Statcast pitch data: seasons and plate-appearance windows.

Every metric is computed on regular-season pitches only. Rate definitions:

- wOBA: FanGraphs definition with FanGraphs season weights
  (``FG_WOBA_WEIGHTS``). Reaching on an error or a fielder's choice earns no
  credit, and the denominator is AB + BB - IBB + SF + HBP, so intentional
  walks, sacrifice bunts, and catcher's interference are excluded. Statcast's
  own per-PA ``woba_value`` differs (it credits reaching on an error and uses
  rounded weights), which inflates wOBA by roughly .005-.010.
- xwOBA: Baseball Savant's ``estimated_woba_using_speedangle`` over the same
  PA; Savant fills it for strikeouts, walks, and HBP, and the rare untracked
  batted ball falls back to its actual wOBA value.
- chase: swings / pitches outside the zone. The zone is plate_x within
  +/-0.83 ft (the plate plus a ball radius) and plate_z between the batter's
  sz_bot and sz_top. ``chase_breaking`` and ``chase_offspeed`` restrict to
  those pitch groups.
- zone_contact: 1 - whiffs / swings on pitches in the zone.
- whiff: whiffs / swings. ``whiff_96plus``, ``whiff_breaking`` and
  ``whiff_two_strike`` restrict the swings to release speed >= 96 mph,
  breaking-ball pitch types, and two-strike counts respectively.
"""

import numpy as np
import pandas as pd

from yanks_analytics.features.pitch_level import classify_pitches

REGULAR_SEASON = "R"

# FanGraphs linear weights (Guts page, retrieved 2026-09-29).
FG_WOBA_WEIGHTS = {
    2017: {"wBB": 0.692994, "wHBP": 0.722619, "w1B": 0.876669, "w2B": 1.23217, "w3B": 1.55212, "wHR": 1.97989},
    2018: {"wBB": 0.68953, "wHBP": 0.720175, "w1B": 0.879531, "w2B": 1.24727, "w3B": 1.57824, "wHR": 2.03083},
    2019: {"wBB": 0.690295, "wHBP": 0.719216, "w1B": 0.869607, "w2B": 1.21666, "w3B": 1.52902, "wHR": 1.93954},
    2020: {"wBB": 0.698811, "wHBP": 0.728443, "w1B": 0.882526, "w2B": 1.2381, "w3B": 1.55812, "wHR": 1.97912},
    2021: {"wBB": 0.691717, "wHBP": 0.721932, "w1B": 0.879055, "w2B": 1.24165, "w3B": 1.56798, "wHR": 2.00652},
    2022: {"wBB": 0.688744, "wHBP": 0.720213, "w1B": 0.883851, "w2B": 1.26148, "w3B": 1.60134, "wHR": 2.072},
    2023: {"wBB": 0.695903, "wHBP": 0.726005, "w1B": 0.882536, "w2B": 1.24376, "w3B": 1.56887, "wHR": 2.0041},
    2024: {"wBB": 0.689131, "wHBP": 0.720192, "w1B": 0.881711, "w2B": 1.25445, "w3B": 1.58991, "wHR": 2.04961},
    2025: {"wBB": 0.691497, "wHBP": 0.722289, "w1B": 0.882406, "w2B": 1.25191, "w3B": 1.58446, "wHR": 2.0374},
    2026: {"wBB": 0.69822, "wHBP": 0.729166, "w1B": 0.890086, "w2B": 1.26144, "w3B": 1.59566, "wHR": 2.0494},
}
EVENT_WEIGHT = {
    "walk": "wBB", "hit_by_pitch": "wHBP", "single": "w1B",
    "double": "w2B", "triple": "w3B", "home_run": "wHR",
}
# PA-ending events that are not in the FanGraphs wOBA denominator.
NON_WOBA_EVENTS = frozenset([
    "intent_walk", "sac_bunt", "sac_bunt_double_play", "catcher_interf", "truncated_pa",
])
PA_KEY = ["game_pk", "at_bat_number"]
PITCH_METRICS = [
    "chase", "chase_breaking", "chase_offspeed", "zone_swing", "zone_contact", "whiff",
    "whiff_96plus", "whiff_breaking", "whiff_two_strike",
]


def regular_season(pitches: pd.DataFrame) -> pd.DataFrame:
    """Keep regular-season pitches and add a datetime ``game_date``."""
    df = pitches[pitches["game_type"] == REGULAR_SEASON].copy()
    df["game_date"] = pd.to_datetime(df["game_date"])
    return df


def plate_appearances(pitches: pd.DataFrame) -> pd.DataFrame:
    """One row per wOBA plate appearance, in chronological order per batter.

    Adds ``xwoba_value`` and ``pa_index`` (0-based order of the PA within
    the batter's career in the data provided).
    """
    pa = pitches[pitches["events"].notna() & ~pitches["events"].isin(NON_WOBA_EVENTS)].copy()
    seasons = pd.to_datetime(pa["game_date"]).dt.year
    weight_key = pa["events"].map(EVENT_WEIGHT)
    pa["woba_value"] = [
        FG_WOBA_WEIGHTS[yr][key] if isinstance(key, str) else 0.0
        for yr, key in zip(seasons, weight_key)
    ]
    pa["woba_denom"] = 1.0
    pa["xwoba_value"] = pa["estimated_woba_using_speedangle"].fillna(pa["woba_value"])
    pa = pa.sort_values(["batter", "game_date", "game_pk", "at_bat_number"])
    pa["pa_index"] = pa.groupby("batter").cumcount()
    return pa[["batter", "game_date", "game_pk", "at_bat_number", "woba_value",
               "woba_denom", "xwoba_value", "pa_index"]]


def _pitch_flags(pitches: pd.DataFrame) -> pd.DataFrame:
    df = classify_pitches(pitches)
    df["out_zone"] = ~df["in_zone"] & df["zone_known"]
    df["velo_96"] = df["release_speed"] >= 96
    df["two_strike"] = df["strikes"] == 2
    df["breaking"] = df["pitch_group"] == "breaking"
    df["offspeed"] = df["pitch_group"] == "offspeed"
    return df


def _rate(numer: pd.Series, denom: pd.Series) -> pd.Series:
    return (numer / denom.where(denom > 0)).astype(float)


def hitter_metrics(pitches: pd.DataFrame, pa: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Aggregate PA outcomes and pitch-level rates by the ``by`` columns.

    ``pitches`` and ``pa`` must both carry the ``by`` columns.
    """
    outcome = pa.assign(
        w=pa["woba_value"], xw=pa["xwoba_value"], d=pa["woba_denom"]
    ).groupby(by).agg(PA=("d", "sum"), w=("w", "sum"), xw=("xw", "sum"))
    outcome["wOBA"] = outcome["w"] / outcome["PA"]
    outcome["xwOBA"] = outcome["xw"] / outcome["PA"]

    f = _pitch_flags(pitches)
    swing, whiff = f["is_swing"], f["is_whiff"]
    parts = pd.DataFrame({
        **{c: f[c] for c in by},
        "pitches": 1,
        "oz": f["out_zone"], "oz_swing": f["out_zone"] & swing,
        "oz_brk": f["out_zone"] & f["breaking"], "oz_brk_swing": f["out_zone"] & f["breaking"] & swing,
        "oz_off": f["out_zone"] & f["offspeed"], "oz_off_swing": f["out_zone"] & f["offspeed"] & swing,
        "iz": f["in_zone"], "iz_swing": f["in_zone"] & swing,
        "iz_whiff": f["in_zone"] & whiff,
        "swing": swing, "whiff": whiff,
        "swing_96": swing & f["velo_96"], "whiff_96": whiff & f["velo_96"],
        "swing_brk": swing & f["breaking"], "whiff_brk": whiff & f["breaking"],
        "swing_2s": swing & f["two_strike"], "whiff_2s": whiff & f["two_strike"],
    })
    s = parts.groupby(by).sum()
    rates = pd.DataFrame({
        "pitches": s["pitches"],
        "chase": _rate(s["oz_swing"], s["oz"]),
        "chase_breaking": _rate(s["oz_brk_swing"], s["oz_brk"]),
        "chase_offspeed": _rate(s["oz_off_swing"], s["oz_off"]),
        "zone_swing": _rate(s["iz_swing"], s["iz"]),
        "zone_contact": 1 - _rate(s["iz_whiff"], s["iz_swing"]),
        "whiff": _rate(s["whiff"], s["swing"]),
        "whiff_96plus": _rate(s["whiff_96"], s["swing_96"]),
        "whiff_breaking": _rate(s["whiff_brk"], s["swing_brk"]),
        "whiff_two_strike": _rate(s["whiff_2s"], s["swing_2s"]),
        "swings_96plus": s["swing_96"],
    })
    return outcome[["PA", "wOBA", "xwOBA"]].join(rates, how="left")


def season_table(pitches: pd.DataFrame) -> pd.DataFrame:
    """Batter-season table (index: batter, season) from regular-season pitches."""
    rs = regular_season(pitches)
    rs["season"] = rs["game_date"].dt.year
    pa = plate_appearances(rs)
    pa["season"] = pa["game_date"].dt.year
    return hitter_metrics(rs, pa, ["batter", "season"])


def pa_window(pitches: pd.DataFrame, start: int, stop: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Pitches and PA rows for each batter's career PA ``start`` <= index < ``stop``.

    ``pitches`` should hold each batter's full MLB career so the PA order is
    a career order. Pitches belong to a PA through (game_pk, at_bat_number).
    """
    rs = regular_season(pitches)
    pa = plate_appearances(rs)
    win = pa[(pa["pa_index"] >= start) & (pa["pa_index"] < stop)]
    keys = win[["batter", *PA_KEY]]
    win_pitches = rs.merge(keys, on=["batter", *PA_KEY], how="inner")
    return win_pitches, win


def window_table(pitches: pd.DataFrame, start: int, stop: int) -> pd.DataFrame:
    """Per-batter metrics over career PA [start, stop); drops batters short of ``stop``."""
    win_pitches, win = pa_window(pitches, start, stop)
    table = hitter_metrics(win_pitches, win, ["batter"])
    return table[table["PA"] >= (stop - start)]


OUTCOME_CUTS = [(0.340, "star"), (0.310, "solid"), (0.280, "disappointing")]


def outcome_label(woba: float) -> str:
    """Label a first-600-PA wOBA: star >= .340, solid >= .310, disappointing >= .280, else bust."""
    for cut, label in OUTCOME_CUTS:
        if woba >= cut:
            return label
    return "bust"


def first_pa_outcomes(pitches: pd.DataFrame, batter_ids, n_pa: int = 600) -> pd.DataFrame:
    """wOBA over each batter's first ``n_pa`` MLB PA, with a label.

    Batters with fewer than ``n_pa`` PA in the data get ``label =
    "insufficient"`` rather than a guessed outcome.
    """
    rs = regular_season(pitches[pitches["batter"].isin(batter_ids)])
    pa = plate_appearances(rs)
    career = pa.groupby("batter")["woba_denom"].sum().rename("career_PA")
    first = pa[pa["pa_index"] < n_pa].groupby("batter").agg(
        w=("woba_value", "sum"), d=("woba_denom", "sum"), through=("game_date", "max")
    )
    out = career.to_frame().join(first)
    out[f"wOBA_first{n_pa}"] = out["w"] / out["d"]
    enough = out["career_PA"] >= n_pa
    out["label"] = np.where(enough, out[f"wOBA_first{n_pa}"].map(outcome_label), "insufficient")
    out["reached_on"] = out["through"].where(enough)
    return out[["career_PA", f"wOBA_first{n_pa}", "label", "reached_on"]]

"""Merge FanGraphs team batting and fielding tables.

The batting and fielding endpoints label teams differently ("NYY" vs
"Yankees"), so the merge goes through ``FG_TEAM_NAME_TO_ABBR`` and is
validated: a wrong alias would otherwise silently drop a team.
"""

import pandas as pd

# FanGraphs team-fielding nickname -> FanGraphs team-batting abbreviation.
# The batting endpoint uses TBR / WSN / CHW (not TB / WSH / CWS).
FG_TEAM_NAME_TO_ABBR = {
    "Angels": "LAA",
    "Astros": "HOU",
    "Athletics": "OAK",
    "Blue Jays": "TOR",
    "Braves": "ATL",
    "Brewers": "MIL",
    "Cardinals": "STL",
    "Cleveland": "CLE",
    "Cubs": "CHC",
    "Diamondbacks": "ARI",
    "Dodgers": "LAD",
    "Giants": "SFG",
    "Guardians": "CLE",
    "Indians": "CLE",
    "Mariners": "SEA",
    "Marlins": "MIA",
    "Mets": "NYM",
    "Nationals": "WSN",
    "Orioles": "BAL",
    "Padres": "SDP",
    "Phillies": "PHI",
    "Pirates": "PIT",
    "Rangers": "TEX",
    "Rays": "TBR",
    "Red Sox": "BOS",
    "Reds": "CIN",
    "Rockies": "COL",
    "Royals": "KCR",
    "Tampa Bay": "TBR",
    "Tigers": "DET",
    "Twins": "MIN",
    "White Sox": "CHW",
    "Yankees": "NYY",
}

ATH_FIRST_SEASON = 2025


def merge_team_batting_fielding(
    batting: pd.DataFrame, fielding: pd.DataFrame
) -> pd.DataFrame:
    """Merge FanGraphs team batting and fielding tables on (Season, team).

    Validates the merge instead of silently dropping mismapped teams.
    """
    fielding = fielding.copy()
    fielding["TeamAbbr"] = fielding["Team"].map(FG_TEAM_NAME_TO_ABBR)
    # FanGraphs abbreviates the Athletics OAK through 2024 and ATH from 2025.
    athletics_2025_on = (fielding["TeamAbbr"] == "OAK") & (fielding["Season"] >= ATH_FIRST_SEASON)
    fielding.loc[athletics_2025_on, "TeamAbbr"] = "ATH"
    unmapped = fielding.loc[fielding["TeamAbbr"].isna(), "Team"].unique()
    if len(unmapped) > 0:
        raise ValueError(f"Unmapped fielding team labels: {sorted(unmapped)}")

    merged = batting.merge(
        fielding[["Season", "TeamAbbr", "OAA", "DRS"]],
        left_on=["Season", "Team"],
        right_on=["Season", "TeamAbbr"],
        how="left",
    )
    missing = merged.loc[merged["OAA"].isna(), ["Season", "Team"]]
    if len(missing) > 0:
        raise ValueError(
            "Team batting/fielding merge dropped OAA for: "
            f"{missing.to_dict('records')}"
        )
    return merged

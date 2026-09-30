"""Statcast and FanGraphs data fetching with local parquet caching.

Usage:
    from yanks_analytics.data.statcast import load_seasons, get_team_batting_stats

    # Regular-season and spring pitches for several seasons (cached after first pull)
    pitches = load_seasons(range(2023, 2027))

    # FanGraphs team batting totals, including baserunning
    batting = get_team_batting_stats(2024)
"""

import os
from pathlib import Path

import pandas as pd

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# Keep pybaseball's own cache inside the project so imports/tests do not write to
# the user's home directory.
os.environ.setdefault("PYBASEBALL_CACHE", str(CACHE_DIR / "pybaseball"))


def _enable_pybaseball_cache() -> None:
    """Enable pybaseball's cache after the local cache path is configured."""
    from pybaseball import cache as pb_cache

    pb_cache.enable()


# Columns the analysis notebooks need; reading only these keeps seven seasons
# of pitch data in memory comfortably.
ANALYSIS_COLUMNS = [
    "batter", "game_date", "game_pk", "at_bat_number", "game_type", "description",
    "plate_x", "plate_z", "sz_bot", "sz_top", "pitch_type", "release_speed", "strikes",
    "events", "woba_value", "woba_denom", "estimated_woba_using_speedangle",
]


def get_statcast_pitches(
    season: int, force: bool = False, columns: list[str] | None = None
) -> pd.DataFrame:
    """Fetch pitch-level Statcast data for a full season.

    Caches results as parquet. A full season is ~700k rows. ``columns``
    limits what is read from the cache.
    """
    cache_path = CACHE_DIR / f"statcast_pitches_{season}.parquet"

    if cache_path.exists() and not force:
        return pd.read_parquet(cache_path, columns=columns)

    _enable_pybaseball_cache()
    from pybaseball import statcast

    print(f"Pulling Statcast pitch data for {season} (this takes a few minutes)...")
    df = statcast(
        start_dt=f"{season}-03-01",  # the 2025 Tokyo Series opened March 18
        end_dt=f"{season}-11-05",
    )
    df.to_parquet(cache_path, index=False)
    print(f"Cached {len(df):,} pitches to {cache_path}")
    return df[columns] if columns is not None else df


def load_seasons(seasons, columns: list[str] | None = None) -> pd.DataFrame:
    """Concatenate cached Statcast seasons (default: ``ANALYSIS_COLUMNS``)."""
    columns = ANALYSIS_COLUMNS if columns is None else columns
    return pd.concat(
        [get_statcast_pitches(season, columns=columns) for season in seasons],
        ignore_index=True,
    )


def get_team_batting_stats(season: int, force: bool = False) -> pd.DataFrame:
    """Fetch team-level batting stats from FanGraphs.

    Includes baserunning (BsR, wSB, UBR, wGDP, SB, CS, Spd) and standard
    offense. Uses the FanGraphs leaders JSON API (the legacy endpoint that
    ``pybaseball.team_batting`` scrapes now returns 403) and renames the
    columns that differ to their familiar FanGraphs names: ``BaseRunning`` ->
    ``BsR``, ``wBsR`` -> ``wSB``, ``GDPRuns`` -> ``wGDP``. ``Team`` holds the
    FanGraphs abbreviation (``"NYY"``).
    """
    cache_path = CACHE_DIR / f"team_batting_{season}.parquet"

    if cache_path.exists() and not force:
        return pd.read_parquet(cache_path)

    print(f"Pulling FanGraphs team batting stats for {season}...")
    df = _fangraphs_team_leaders(season, stats="bat", type_=8, sortstat="WAR")
    df = df.drop(columns=["Team"]).rename(columns={
        "TeamNameAbb": "Team", "BaseRunning": "BsR", "wBsR": "wSB", "GDPRuns": "wGDP",
    })
    df["Season"] = season
    df.to_parquet(cache_path, index=False)
    print(f"Cached {len(df)} teams to {cache_path}")
    return df


def _fangraphs_team_leaders(season: int, stats: str, type_: int, sortstat: str) -> pd.DataFrame:
    """One season of FanGraphs team leaders from the JSON API."""
    import requests

    response = requests.get(
        "https://www.fangraphs.com/api/leaders/major-league/data",
        params={
            "age": "", "pos": "all", "stats": stats, "lg": "all", "qual": "0",
            "season": str(season), "season1": str(season), "startdate": "",
            "enddate": "", "month": "0", "hand": "", "team": "0,ts",
            "pageitems": "500", "pagenum": "1", "ind": "0", "rost": "0",
            "players": "0", "type": str(type_), "postseason": "",
            "sortdir": "default", "sortstat": sortstat,
        },
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        },
        timeout=30,
    )
    response.raise_for_status()
    return pd.DataFrame(response.json()["data"])


def get_team_fielding_stats(season: int, force: bool = False) -> pd.DataFrame:
    """Fetch team-level fielding stats from FanGraphs.

    Includes OAA, DRS, UZR, and Def. Note that FanGraphs labels teams by
    nickname here (``"Yankees"``), unlike the abbreviations in
    :func:`get_team_batting_stats` (``"NYY"``) — see
    ``yanks_analytics.features.team_value.FG_TEAM_NAME_TO_ABBR`` for the merge map.

    Uses the modern FanGraphs leaders JSON API directly because the legacy
    ``leaders-legacy.aspx`` endpoint that ``pybaseball.team_fielding`` scrapes
    now returns 403.
    """
    cache_path = CACHE_DIR / f"team_fielding_{season}.parquet"

    if cache_path.exists() and not force:
        return pd.read_parquet(cache_path)

    print(f"Pulling FanGraphs team fielding stats for {season}...")
    df = _fangraphs_team_leaders(season, stats="fld", type_=1, sortstat="Defense")
    # Match the column naming of pybaseball.team_fielding: nickname in
    # "Team" ("Yankees") and FanGraphs "Def" for the defensive runs total.
    df = df.drop(columns=["Team"]).rename(columns={"TeamName": "Team", "Defense": "Def"})
    df.to_parquet(cache_path, index=False)
    print(f"Cached {len(df)} teams to {cache_path}")
    return df

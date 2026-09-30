"""Curated prospect cohort: player IDs, MLB debut dates, and developing org.

A hand-curated cohort of 43 hitting prospects who debuted 2020-2025. It is
not a systematic sample (it is not, for example, every top-100 prospect), so
cohort-level results describe these players rather than all prospects.

MLBAM IDs and debut dates are verified against the MLB Stats API
(/api/v1/people, ``mlbDebutDate``), retrieved 2026-09-29. Outcomes are not
hand-labeled: they are computed from Statcast in
``yanks_analytics.features.season.first_pa_outcomes``.

"org" is the organization that developed the player, not necessarily the
current team.
"""

import pandas as pd

# fmt: off
# Columns: name, mlbam_id, mlb_debut (YYYY-MM-DD), org
PROSPECT_DATA = [
    # === Yankees ===
    ("Anthony Volpe",       683011, "2023-03-30", "NYY"),
    ("Jasson Dominguez",    691176, "2023-09-01", "NYY"),
    ("Ben Rice",            700250, "2024-06-18", "NYY"),
    ("Oswald Peraza",       672724, "2022-09-02", "NYY"),
    ("Everson Pereira",     677592, "2023-08-22", "NYY"),
    ("Austin Wells",        669224, "2023-09-01", "NYY"),
    # === Comparison organizations ===
    ("Gunnar Henderson",    683002, "2022-08-31", "BAL"),
    ("Adley Rutschman",     668939, "2022-05-21", "BAL"),
    ("Colton Cowser",       681297, "2023-07-05", "BAL"),
    ("Heston Kjerstad",     677008, "2023-09-14", "BAL"),
    ("Jordan Westburg",     676059, "2023-06-26", "BAL"),
    ("Nolan Jones",         666134, "2022-07-08", "CLE"),
    ("Steven Kwan",         680757, "2022-04-07", "CLE"),
    ("Bo Naylor",           666310, "2022-10-01", "CLE"),
    ("Tyler Freeman",       671289, "2022-08-03", "CLE"),
    ("Brayan Rocchio",      677587, "2023-05-16", "CLE"),
    ("Andy Pages",          681624, "2024-04-16", "LAD"),
    ("James Outman",        681546, "2022-07-31", "LAD"),
    ("Miguel Vargas",       678246, "2022-08-03", "LAD"),
    ("Josh Lowe",           666139, "2021-09-08", "TB"),
    ("Curtis Mead",         678554, "2023-08-04", "TB"),
    ("Junior Caminero",     691406, "2023-09-23", "TB"),
    ("Michael Harris II",   671739, "2022-05-28", "ATL"),
    ("Vaughn Grissom",      687093, "2022-08-10", "ATL"),
    ("Cristian Pache",      665506, "2020-08-21", "ATL"),
    # === Other organizations ===
    ("Julio Rodriguez",     677594, "2022-04-08", "SEA"),
    ("Bobby Witt Jr.",      677951, "2022-04-07", "KC"),
    ("Corbin Carroll",      682998, "2022-08-29", "ARI"),
    ("Riley Greene",        682985, "2022-06-18", "DET"),
    ("CJ Abrams",           682928, "2022-04-08", "SD"),
    ("Elly De La Cruz",     682829, "2023-06-06", "CIN"),
    ("Jackson Chourio",     694192, "2024-03-29", "MIL"),
    ("Marcelo Mayer",       691785, "2025-05-24", "BOS"),
    ("Spencer Torkelson",   679529, "2022-04-08", "DET"),
    ("Jordyn Adams",        677941, "2023-08-02", "LAA"),
    ("Josh Jung",           673962, "2022-09-09", "TEX"),
    ("Ezequiel Tovar",      678662, "2022-09-23", "COL"),
    ("Jordan Walker",       691023, "2023-03-30", "STL"),
    ("Matt McLain",         680574, "2023-05-15", "CIN"),
    ("Brooks Lee",          686797, "2024-07-03", "MIN"),
    ("Joey Bart",           663698, "2020-08-20", "SF"),
    ("Jarred Kelenic",      672284, "2021-05-13", "SEA"),
    ("Nick Madrigal",       663611, "2020-07-31", "CHW"),
]
# fmt: on

YANKEES_ORG = "NYY"
# Five organizations with strong public player-development reputations,
# chosen when the cohort was assembled. The choice is an assumption, not a
# finding, and the per-org samples (3-5 players) are too small to rank orgs.
COMPARISON_ORGS = ("BAL", "CLE", "LAD", "TB", "ATL")


def get_prospect_df() -> pd.DataFrame:
    """Return the cohort as a DataFrame with a parsed debut date and year."""
    df = pd.DataFrame(PROSPECT_DATA, columns=["name", "mlbam_id", "mlb_debut", "org"])
    df["mlb_debut"] = pd.to_datetime(df["mlb_debut"])
    df["debut_year"] = df["mlb_debut"].dt.year
    return df


def get_prospect_ids() -> dict[str, int]:
    """Return {name: mlbam_id} for all tracked prospects."""
    return {name: mid for name, mid, *_ in PROSPECT_DATA}


def get_org_prospects(org: str) -> pd.DataFrame:
    """Return prospects developed by a specific organization."""
    df = get_prospect_df()
    return df[df["org"] == org]


# MiLB season totals across levels, from the MLB Stats API
# (/api/v1/people/{id}/stats?stats=yearByYear&group=hitting, sportId 11-14),
# retrieved 2026-09-29. Rates are computed from counting stats.
MILB_STATS = {
    "Anthony Volpe": {
        2021: {"level": "A/A+", "g": 109, "pa": 513, "avg": 0.294, "obp": 0.423, "slg": 0.604,
               "hr": 27, "bb_pct": 0.152, "k_pct": 0.197},
        2022: {"level": "AA/AAA", "g": 132, "pa": 596, "avg": 0.249, "obp": 0.342, "slg": 0.460,
               "hr": 21, "bb_pct": 0.109, "k_pct": 0.198},
    },
    "Jasson Dominguez": {
        2022: {"level": "A/A+/AA", "g": 120, "pa": 530, "avg": 0.273, "obp": 0.375, "slg": 0.461,
               "hr": 16, "bb_pct": 0.136, "k_pct": 0.242},
        2023: {"level": "AA/AAA", "g": 118, "pa": 544, "avg": 0.265, "obp": 0.377, "slg": 0.425,
               "hr": 15, "bb_pct": 0.153, "k_pct": 0.244},
        2024: {"level": "A/AA/AAA", "g": 58, "pa": 250, "avg": 0.314, "obp": 0.376, "slg": 0.504,
               "hr": 11, "bb_pct": 0.088, "k_pct": 0.200},
    },
    "Gunnar Henderson": {
        2021: {"level": "A/A+/AA", "g": 105, "pa": 463, "avg": 0.258, "obp": 0.350, "slg": 0.476,
               "hr": 17, "bb_pct": 0.121, "k_pct": 0.309},
        2022: {"level": "AA/AAA", "g": 112, "pa": 503, "avg": 0.297, "obp": 0.416, "slg": 0.531,
               "hr": 19, "bb_pct": 0.157, "k_pct": 0.231},
    },
    "Corbin Carroll": {
        2022: {"level": "AA/AAA", "g": 91, "pa": 434, "avg": 0.303, "obp": 0.422, "slg": 0.604,
               "hr": 23, "bb_pct": 0.150, "k_pct": 0.240},
    },
    "Bobby Witt Jr.": {
        2021: {"level": "AA/AAA", "g": 123, "pa": 564, "avg": 0.290, "obp": 0.361, "slg": 0.575,
               "hr": 33, "bb_pct": 0.090, "k_pct": 0.232},
    },
    "Oswald Peraza": {
        2022: {"level": "AAA", "g": 99, "pa": 429, "avg": 0.259, "obp": 0.329, "slg": 0.448,
               "hr": 19, "bb_pct": 0.079, "k_pct": 0.233},
    },
    "Ben Rice": {
        2022: {"level": "A", "g": 68, "pa": 243, "avg": 0.267, "obp": 0.368, "slg": 0.442,
               "hr": 9, "bb_pct": 0.115, "k_pct": 0.169},
        2023: {"level": "A/A+/AA", "g": 73, "pa": 332, "avg": 0.324, "obp": 0.434, "slg": 0.615,
               "hr": 20, "bb_pct": 0.133, "k_pct": 0.187},
        2024: {"level": "AA/AAA", "g": 79, "pa": 356, "avg": 0.273, "obp": 0.400, "slg": 0.567,
               "hr": 24, "bb_pct": 0.160, "k_pct": 0.202},
    },
}

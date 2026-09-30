"""Tests for prospect cohort data integrity."""

import pandas as pd

from yanks_analytics.data.prospects import (
    COMPARISON_ORGS,
    MILB_STATS,
    PROSPECT_DATA,
    YANKEES_ORG,
    get_org_prospects,
    get_prospect_df,
    get_prospect_ids,
)


class TestProspectData:
    def test_cohort_size(self):
        assert len(PROSPECT_DATA) == 43

    def test_tuple_format(self):
        for name, mlbam_id, debut, org in PROSPECT_DATA:
            assert isinstance(name, str)
            assert isinstance(mlbam_id, int) and mlbam_id > 0
            assert 2020 <= pd.Timestamp(debut).year <= 2025
            assert isinstance(org, str) and 2 <= len(org) <= 3

    def test_no_duplicate_names_or_ids(self):
        names = [name for name, *_ in PROSPECT_DATA]
        ids = [mid for _, mid, *_ in PROSPECT_DATA]
        assert len(names) == len(set(names))
        assert len(ids) == len(set(ids))

    def test_corrected_ids(self):
        # 670770 is TJ Friedl and 678545 is Osleivis Basabe (MLB Stats API).
        ids = get_prospect_ids()
        assert ids["Austin Wells"] == 669224
        assert ids["Ezequiel Tovar"] == 678662


class TestGetProspectDf:
    def test_columns(self):
        df = get_prospect_df()
        assert set(df.columns) == {"name", "mlbam_id", "mlb_debut", "org", "debut_year"}

    def test_debut_year_derived_from_date(self):
        df = get_prospect_df().set_index("name")
        assert df.loc["Ben Rice", "debut_year"] == 2024
        assert df.loc["Josh Lowe", "debut_year"] == 2021


class TestOrgs:
    def test_yankees_group(self):
        assert len(get_org_prospects(YANKEES_ORG)) == 6

    def test_comparison_orgs_present(self):
        orgs = set(get_prospect_df()["org"])
        assert set(COMPARISON_ORGS) <= orgs


class TestMilbStats:
    def test_players_are_in_cohort(self):
        assert set(MILB_STATS) <= set(get_prospect_ids())

    def test_fields_and_rates(self):
        for player, seasons in MILB_STATS.items():
            for year, s in seasons.items():
                assert {"level", "g", "pa", "avg", "obp", "slg", "hr", "bb_pct", "k_pct"} <= set(s)
                assert 0 < s["bb_pct"] < 0.30, f"{player} {year}"
                assert 0 < s["k_pct"] < 0.50, f"{player} {year}"
                assert s["avg"] <= s["obp"] and s["avg"] <= s["slg"]

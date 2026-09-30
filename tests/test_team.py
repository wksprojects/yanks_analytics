"""Tests for the FanGraphs team batting/fielding merge."""

import pandas as pd
import pytest

from yanks_analytics.features.team import (
    FG_TEAM_NAME_TO_ABBR,
    merge_team_batting_fielding,
)


class TestTeamNameMap:
    def test_uses_fangraphs_batting_abbreviations(self):
        # The FanGraphs batting endpoint uses TBR/WSN/CHW. The old notebook
        # maps emitted TB/WSH/CWS, silently dropping three teams per season.
        assert FG_TEAM_NAME_TO_ABBR["Rays"] == "TBR"
        assert FG_TEAM_NAME_TO_ABBR["Nationals"] == "WSN"
        assert FG_TEAM_NAME_TO_ABBR["White Sox"] == "CHW"

    def test_covers_30_franchises(self):
        # Aliases (Indians/Guardians/Cleveland, Rays/Tampa Bay) collapse to
        # exactly 30 distinct abbreviations.
        assert len(set(FG_TEAM_NAME_TO_ABBR.values())) == 30


class TestMergeTeamBattingFielding:
    def _frames(self):
        batting = pd.DataFrame({
            "Season": [2024, 2024],
            "Team": ["NYY", "TBR"],
            "WAR": [40.0, 30.0],
        })
        fielding = pd.DataFrame({
            "Season": [2024, 2024],
            "Team": ["Yankees", "Rays"],
            "OAA": [10.0, 20.0],
            "DRS": [5.0, 15.0],
        })
        return batting, fielding

    def test_merges_all_teams(self):
        batting, fielding = self._frames()
        merged = merge_team_batting_fielding(batting, fielding)
        assert len(merged) == 2
        assert merged["OAA"].notna().all()

    def test_raises_on_unmapped_fielding_label(self):
        batting, fielding = self._frames()
        fielding.loc[1, "Team"] = "Devil Rays"
        with pytest.raises(ValueError, match="Unmapped"):
            merge_team_batting_fielding(batting, fielding)

    def test_raises_when_merge_drops_a_team(self):
        batting, fielding = self._frames()
        fielding = fielding.iloc[:1]  # no Rays fielding row
        with pytest.raises(ValueError, match="dropped OAA"):
            merge_team_batting_fielding(batting, fielding)


class TestAthleticsAbbreviation:
    def _frames(self, season):
        batting = pd.DataFrame({"Season": [season], "Team": ["ATH" if season >= 2025 else "OAK"]})
        fielding = pd.DataFrame({"Season": [season], "Team": ["Athletics"], "OAA": [1.0], "DRS": [2.0]})
        return batting, fielding

    @pytest.mark.parametrize("season", [2024, 2025])
    def test_athletics_merge_across_relocation(self, season):
        merged = merge_team_batting_fielding(*self._frames(season))
        assert merged.loc[0, "OAA"] == 1.0

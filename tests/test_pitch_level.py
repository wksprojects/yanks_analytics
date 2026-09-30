"""Tests for pitch classification."""

import numpy as np
import pandas as pd

from yanks_analytics.features.pitch_level import classify_pitches


class TestClassifyPitches:
    def _frame(self, **overrides):
        base = {
            "description": ["called_strike"],
            "pitch_type": ["FF"],
            "plate_x": [0.0],
            "plate_z": [2.5],
            "sz_top": [3.5],
            "sz_bot": [1.5],
        }
        base.update(overrides)
        return pd.DataFrame(base)

    def test_swing_and_whiff_classification(self):
        df = self._frame(
            description=["swinging_strike", "foul", "hit_into_play", "called_strike", "ball"],
            pitch_type=["FF"] * 5,
            plate_x=[0.0] * 5, plate_z=[2.5] * 5, sz_top=[3.5] * 5, sz_bot=[1.5] * 5,
        )
        out = classify_pitches(df)
        assert out["is_swing"].tolist() == [True, True, True, False, False]
        assert out["is_whiff"].tolist() == [True, False, False, False, False]

    def test_pitch_group_mapping(self):
        df = self._frame(
            description=["ball"] * 6,
            pitch_type=["FF", "SI", "SL", "CU", "CH", "KN"],
            plate_x=[0.0] * 6, plate_z=[2.5] * 6, sz_top=[3.5] * 6, sz_bot=[1.5] * 6,
        )
        out = classify_pitches(df)
        assert out["pitch_group"].tolist() == [
            "fastball", "fastball", "breaking", "breaking", "offspeed", "other"
        ]

    def test_zone_classification(self):
        df = self._frame(
            description=["ball"] * 5,
            pitch_type=["FF"] * 5,
            plate_x=[0.0, 1.0, 0.0, 0.0, 0.83],
            plate_z=[2.5, 2.5, 4.0, 1.0, 2.5],
            sz_top=[3.5] * 5, sz_bot=[1.5] * 5,
        )
        out = classify_pitches(df)
        # center, outside right, above, below, on the edge (inclusive)
        assert out["in_zone"].tolist() == [True, False, False, False, True]

    def test_unknown_zone_flagged(self):
        df = self._frame(plate_x=[np.nan])
        out = classify_pitches(df)
        assert not out["zone_known"].iloc[0]
        assert not out["in_zone"].iloc[0]


# --- Integration tests with synthetic pitch data ---


class TestPitchGroups:
    def test_sweeper_is_breaking(self):
        from yanks_analytics.features.pitch_level import PITCH_GROUPS
        assert "ST" in PITCH_GROUPS["breaking"]

    def test_screwball_is_offspeed(self):
        from yanks_analytics.features.pitch_level import PITCH_GROUPS
        assert "SC" in PITCH_GROUPS["offspeed"]
        assert "SC" not in PITCH_GROUPS["breaking"]

    def test_groups_are_disjoint(self):
        from yanks_analytics.features.pitch_level import PITCH_GROUPS
        codes = [c for group in PITCH_GROUPS.values() for c in group]
        assert len(codes) == len(set(codes))

"""Tests for season and PA-window hitter tables."""

import numpy as np
import pandas as pd
import pytest

from yanks_analytics.features.season import (
    FG_WOBA_WEIGHTS,
    first_pa_outcomes,
    hitter_metrics,
    outcome_label,
    pa_window,
    plate_appearances,
    regular_season,
    season_table,
)

SINGLE_2024 = FG_WOBA_WEIGHTS[2024]["w1B"]
WALK_2025 = FG_WOBA_WEIGHTS[2025]["wBB"]


def _pitch(batter, date, game, ab, desc, *, x=0.0, z=2.5, pitch_type="FF", speed=94.0,
           strikes=0, event=None, woba=np.nan, denom=np.nan, xwoba=np.nan, game_type="R"):
    return {
        "batter": batter, "game_date": date, "game_pk": game, "at_bat_number": ab,
        "description": desc, "plate_x": x, "plate_z": z, "sz_bot": 1.5, "sz_top": 3.5,
        "pitch_type": pitch_type, "release_speed": speed, "strikes": strikes,
        "events": event, "woba_value": woba, "woba_denom": denom,
        "estimated_woba_using_speedangle": xwoba, "game_type": game_type,
    }


@pytest.fixture
def pitches():
    rows = [
        # PA 1 (2024): out-of-zone take, in-zone whiff on 97 mph, single
        _pitch(1, "2024-04-01", 10, 1, "ball", x=1.5),
        _pitch(1, "2024-04-01", 10, 1, "swinging_strike", speed=97.0),
        _pitch(1, "2024-04-01", 10, 1, "hit_into_play", event="single",
               woba=0.9, denom=1, xwoba=0.5),
        # PA 2 (2024): chase on a sweeper with two strikes, strikeout
        _pitch(1, "2024-04-02", 11, 3, "swinging_strike", x=1.5, pitch_type="ST",
               strikes=2, event="strikeout", woba=0.0, denom=1, xwoba=0.0),
        # PA 3 (2025): walk; xwOBA missing falls back to actual
        _pitch(1, "2025-04-01", 20, 2, "ball", x=-1.5, event="walk", woba=0.7, denom=1),
        # Spring training PA is excluded everywhere
        _pitch(1, "2024-03-01", 5, 1, "hit_into_play", event="home_run",
               woba=2.0, denom=1, xwoba=2.0, game_type="S"),
        # Intentional walk carries no denominator
        _pitch(1, "2025-04-02", 21, 1, "intent_ball", x=2.0, event="intent_walk",
               woba=0.4, denom=np.nan),
    ]
    return pd.DataFrame(rows)


class TestPlateAppearances:
    def test_orders_and_excludes_non_woba_rows(self, pitches):
        pa = plate_appearances(regular_season(pitches))
        assert list(pa["pa_index"]) == [0, 1, 2]
        assert list(pa["woba_value"]) == pytest.approx([SINGLE_2024, 0.0, WALK_2025])

    def test_xwoba_falls_back_to_actual(self, pitches):
        pa = plate_appearances(regular_season(pitches))
        assert list(pa["xwoba_value"]) == pytest.approx([0.5, 0.0, WALK_2025])

    def test_reached_on_error_earns_no_credit(self):
        rows = pd.DataFrame([_pitch(2, "2024-05-01", 30, 1, "hit_into_play", event="field_error",
                                    woba=0.9, denom=1, xwoba=0.2)])
        pa = plate_appearances(regular_season(rows))
        assert list(pa["woba_value"]) == [0.0]

    def test_catcher_interference_not_in_denominator(self):
        rows = pd.DataFrame([_pitch(2, "2024-05-01", 30, 1, "foul", event="catcher_interf",
                                    woba=0.7, denom=1)])
        assert plate_appearances(regular_season(rows)).empty


class TestSeasonTable:
    def test_rates_by_season(self, pitches):
        t = season_table(pitches).loc[(1, 2024)]
        assert t["PA"] == 2
        assert t["wOBA"] == pytest.approx(SINGLE_2024 / 2)
        assert t["xwOBA"] == pytest.approx(0.25)
        assert t["chase"] == pytest.approx(0.5)          # 1 swing on 2 out-of-zone pitches
        assert t["chase_breaking"] == pytest.approx(1.0)  # the chased pitch was a sweeper
        assert np.isnan(t["chase_offspeed"])             # no out-of-zone offspeed pitches
        assert t["zone_contact"] == pytest.approx(0.5)   # 1 whiff on 2 in-zone swings
        assert t["whiff"] == pytest.approx(2 / 3)
        assert t["whiff_96plus"] == pytest.approx(1.0)
        assert t["whiff_breaking"] == pytest.approx(1.0)  # sweeper counts as breaking
        assert t["whiff_two_strike"] == pytest.approx(1.0)

    def test_spring_training_excluded(self, pitches):
        t = season_table(pitches)
        assert t.loc[(1, 2024), "wOBA"] < 2.0

    def test_undefined_rates_are_nan(self, pitches):
        t = season_table(pitches).loc[(1, 2025)]
        assert t["PA"] == 1
        assert np.isnan(t["whiff"])


class TestPaWindow:
    def test_window_selects_pitches_of_those_pa(self, pitches):
        win_pitches, win = pa_window(pitches, 1, 3)
        assert list(win["pa_index"]) == [1, 2]
        assert set(zip(win_pitches["game_pk"], win_pitches["at_bat_number"])) == {(11, 3), (20, 2)}

    def test_hitter_metrics_matches_window(self, pitches):
        win_pitches, win = pa_window(pitches, 0, 2)
        t = hitter_metrics(win_pitches, win, ["batter"]).loc[1]
        assert t["PA"] == 2 and t["wOBA"] == pytest.approx(SINGLE_2024 / 2)


class TestOutcomes:
    @pytest.mark.parametrize("woba,label", [
        (0.340, "star"), (0.3399, "solid"), (0.310, "solid"),
        (0.2999, "disappointing"), (0.280, "disappointing"), (0.2799, "bust"),
    ])
    def test_cut_points(self, woba, label):
        assert outcome_label(woba) == label

    def test_insufficient_sample_is_not_labeled(self, pitches):
        out = first_pa_outcomes(pitches, [1], n_pa=600)
        assert out.loc[1, "label"] == "insufficient"
        assert out.loc[1, "career_PA"] == 3

    def test_label_when_sample_reached(self, pitches):
        out = first_pa_outcomes(pitches, [1], n_pa=2)
        assert out.loc[1, "wOBA_first2"] == pytest.approx(SINGLE_2024 / 2)
        assert out.loc[1, "label"] == "star"


def test_96_mph_boundary_counts_as_96_plus(pitches):
    rows = pd.DataFrame([_pitch(3, "2024-06-01", 40, 1, "swinging_strike", speed=96.0,
                                event="strikeout", woba=0.0, denom=1, xwoba=0.0)])
    assert season_table(rows).loc[(3, 2024), "whiff_96plus"] == 1.0

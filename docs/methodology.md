# Methodology

## Data

| Source | Access | Coverage | Notes |
| --- | --- | --- | --- |
| Statcast pitch data | `pybaseball.statcast`, cached as parquet | 2020–2026 | Pulled from March 1 through early November each season; analyses keep regular-season games (`game_type == "R"`). |
| Savant expected statistics | `pybaseball.statcast_batter_expected_stats` | 2021–2026 | Used only to validate computed wOBA and xwOBA. |
| FanGraphs team leaders | `https://www.fangraphs.com/api/leaders/major-league/data` | 2017–2026 | Team batting (`type=8`) and fielding (`type=1`). The API labels BsR as `BaseRunning`, wSB as `wBsR`, and wGDP as `GDPRuns`; they are renamed on load. UBR is not returned for 2025–2026. |
| FanGraphs Guts | Season constants page | 2017–2026 | wOBA linear weights, stored in `features/season.py`. |
| MLB Stats API | `https://statsapi.mlb.com/api/v1/` | Current | Player IDs, debut dates, draft slots, minor-league season totals (`sportId` 11–14), and transactions. |

## Plate appearances and wOBA

A plate appearance is any regular-season pitch row with a PA-ending `events` value, except intentional walks, sacrifice bunts, catcher's interference, and truncated PA. This matches the FanGraphs wOBA denominator (AB + BB − IBB + SF + HBP).

wOBA is the sum of FanGraphs season weights for unintentional walks, HBP, singles, doubles, triples, and home runs, divided by that denominator. Reaching on an error and fielder's choices earn no credit. Statcast's own per-PA `woba_value` is not used because it credits reaching on an error and uses rounded weights.

xwOBA is Savant's `estimated_woba_using_speedangle` over the same plate appearances. Savant fills it for strikeouts, walks, and HBP; the few batted balls without a tracked estimate fall back to their actual wOBA value.

**Validation:** computed wOBA matches Savant's published value to within .0005 for every hitter with 300+ PA in each season from 2021 to 2026; xwOBA matches with a mean absolute difference under .001 (notebook 02). Computed PA can run a few below official totals when Statcast is missing a pitch record.

## Pitch-level rates

| Metric | Definition |
| --- | --- |
| Zone | `plate_x` within ±0.83 ft (plate plus ball radius) and `plate_z` between the batter's `sz_bot` and `sz_top` |
| Chase | Swings / pitches outside the zone |
| Breaking / offspeed chase | Chase restricted to breaking-ball or offspeed pitch types |
| Zone swing | Swings / pitches in the zone |
| Zone contact | 1 − whiffs / swings on pitches in the zone |
| Whiff | Whiffs / swings |
| Whiff vs 96+ | Whiffs / swings on pitches with release speed ≥ 96.0 mph |
| Breaking-ball whiff | Whiffs / swings on breaking-ball pitch types |
| Two-strike whiff | Whiffs / swings with two strikes |

Swings are swinging strikes (including blocked), fouls, foul tips, foul bunts, and balls in play. Pitch groups: fastball (FF, SI, FC); breaking (SL, ST, CU, KC, SV, CS); offspeed (CH, FS, FO, SC).

## Outcomes

Each cohort player's outcome is his wOBA over his first 600 MLB regular-season plate appearances, in chronological order from his debut. Labels: star ≥ .340, solid ≥ .310, disappointing ≥ .280, bust < .280. Players with fewer than 600 career PA are labeled insufficient and excluded from labeled comparisons.

## Designs

- **Year-to-year stability (notebook 02):** hitters with 300+ PA in consecutive regular seasons from 2021→2022 through 2025→2026. Correlations carry 95% intervals from a bootstrap that resamples hitters. Forecasting models are ordinary least squares scored with 5-fold cross-validation grouped by hitter, so no hitter appears in both training and test folds.
- **Early signals (notebook 03):** signals from each player's first 250 MLB PA; outcome is wOBA over PA 251–850. Only players with 850+ career PA are included. Spearman correlations with 95% player-bootstrap intervals.
- **Readiness gates (notebook 03):** a gate is passed when the early-window value beats the median of qualified MLB batter-seasons (300+ PA, 2021–2026) for breaking-ball chase, offspeed chase, whiff vs 96+, overall chase (lower is better), and zone contact (higher is better). Thresholds use no outcome information.
- **Team context (notebook 05):** FanGraphs team totals with MLB ranks (1 = best) per season. Batting and fielding tables are joined through a validated name map that accounts for the Athletics' abbreviation change (OAK through 2024, ATH from 2025).

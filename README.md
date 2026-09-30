# Yankees Hitter Development: A Public-Data Case Study

Which early signals about a young hitter carry forward, and which only look like they should? This project tests that question league-wide, applies it to a 43-player prospect cohort, and uses it to describe four Yankees-developed hitters (Ben Rice, Anthony Volpe, Jasson Dominguez, and Oswald Peraza) through the 2026 season.

Everything is built from public Statcast, FanGraphs, and MLB Stats API data, and every number in this README is produced by the notebooks. It is an observational study: it describes what happened and tests what predicts it, and it does not claim to explain development decisions that public data cannot see.

Portfolio page: https://wksprojects.com/baseball-analytics-case-study/

## Key findings

| Question | Result | Where |
| --- | --- | --- |
| Is plate discipline stable from season to season? | Yes. Across 990 consecutive-season pairs (300+ PA, 2021–2026), whiff rate repeats at r = .87 and chase, zone swing, and zone contact rates at r = .81, far above wOBA (.47) or xwOBA (.66). | [02](notebooks/02_metric_stability.ipynb) |
| Does discipline help forecast next season's wOBA? | Not beyond contact quality. Adding nine discipline metrics to wOBA and xwOBA moves cross-validated R² from .278 to .271; discipline alone explains about 5%. | [02](notebooks/02_metric_stability.ipynb) |
| Do a prospect's first 250 MLB PA predict his next 600? | Weakly, through production rather than approach. Early wOBA: ρ = .36 (95% CI .02 to .63). Early chase rates: ρ between −.02 and .05. n = 35. | [03](notebooks/03_prospect_early_signals.ipynb) |
| Does a five-gate readiness checklist identify who will produce? | No. Gates passed in the first 250 PA vs. wOBA over the next 600: ρ = −.18 (95% CI −.51 to .18), with flat group means from zero gates to five. | [03](notebooks/03_prospect_early_signals.ipynb) |
| How have the four Yankees-developed hitters moved? | Rice's xwOBA led his results (.338 xwOBA vs .269 wOBA in his 2024 debut), then his wOBA rose to .358 and .384 and he made the 2026 All-Star team. Volpe's wOBA has held between .286 and .297 in all four seasons despite a lower chase rate since 2025. Dominguez's sample remains short and interrupted. | [04](notebooks/04_yankees_case_study.ipynb) |
| What happened to Yankees baserunning? | BsR fell from +7.5 (7th in MLB, 2017) to −17.1 (30th, 2024), mostly through UBR (−31.8 of −38.7 runs in 2021–2024), then recovered to +3.7 (12th) in 2026 with 153 steals. | [05](notebooks/05_team_baserunning_defense.ipynb) |

The through-line: plate discipline is a real and stable skill, but on its own it is weak evidence about future production. Contact quality carries more of the forecast, and a discipline-based readiness checklist did not survive an honest test.

## Notebooks

| Notebook | Focus |
| --- | --- |
| [01 · Cohort and outcomes](notebooks/01_cohort_and_outcomes.ipynb) | The 43-player cohort and one outcome definition: wOBA over the first 600 MLB PA. |
| [02 · Metric stability](notebooks/02_metric_stability.ipynb) | League-wide year-to-year stability and next-season forecasting, plus validation of the computed rates against Baseball Savant. |
| [03 · Prospect early signals](notebooks/03_prospect_early_signals.ipynb) | First 250 PA vs. the next 600, and the readiness-gate test. |
| [04 · Yankees case study](notebooks/04_yankees_case_study.ipynb) | Rice, Volpe, Dominguez, and Peraza: arrival, minor-league lines, MLB seasons, and 2026 roster moves. |
| [05 · Team baserunning and defense](notebooks/05_team_baserunning_defense.ipynb) | Yankees BsR, UBR, wSB, OAA, and DRS with MLB ranks, 2017–2026. |

Notebooks are committed with their outputs, so tables and figures render on GitHub.

## Data and definitions

| Source | Coverage | Use |
| --- | --- | --- |
| Statcast pitch data (Baseball Savant via `pybaseball`) | 2020–2026 regular seasons | Plate appearances, wOBA, xwOBA, and pitch-level discipline rates |
| Baseball Savant expected-statistics leaderboard | 2021–2026 | Validation of computed wOBA and xwOBA |
| FanGraphs leaders API | 2017–2026 team totals | BsR, wSB, UBR, SB, OAA, DRS |
| FanGraphs Guts | 2017–2026 | Season wOBA weights |
| MLB Stats API | Current | Player IDs, debut dates, draft slots, minor-league lines, transactions |

- **wOBA** follows the FanGraphs definition with FanGraphs season weights: no credit for reaching on an error, and intentional walks, sacrifice bunts, and catcher's interference excluded from the denominator. Computed values match Savant's published wOBA to within .0005 for every qualified hitter in 2021–2026 (notebook 02).
- **Plate discipline** rates use a strike zone of the plate width plus a ball radius (±0.83 ft) and each batter's Statcast zone top and bottom. Breaking balls include sweepers (`ST`).
- **Outcome labels** are computed, not assigned: wOBA over the first 600 MLB PA, labeled star (≥ .340), solid (≥ .310), disappointing (≥ .280), or bust. Players short of 600 PA are labeled insufficient.

Full definitions are in [docs/methodology.md](docs/methodology.md).

## What this project does not claim

- It does not rank organizations. The cohort is hand-picked, with three to six players per organization.
- It does not attribute outcomes to coaching, development programs, or front-office decisions. Public data cannot see those.
- Small samples are reported as small. The prospect analyses rest on 35 players, and their confidence intervals are shown.

See [docs/limitations.md](docs/limitations.md).

## Corrections made during review

This project was rebuilt after a line-by-line audit. The changes are listed because they are part of the method:

- Two cohort players' IDs pointed at other players, and six debut years were wrong. All IDs and debut dates now come from the MLB Stats API.
- Outcome labels had been assigned by hand, and 18 of 43 did not follow the project's own stated rule. They are now computed in code.
- Hand-entered prospect rankings with no verifiable source were removed.
- Sweepers were missing from breaking-ball metrics because Statcast's sweeper code (`ST`) was not mapped.
- Statcast's per-PA `woba_value`, which credits reaching on an error, had been used as wOBA. It is replaced by the FanGraphs definition and validated against Savant.
- Season pulls began March 20 and missed the 2025 Tokyo Series (March 18–19).
- Readiness-gate thresholds had been set from the players already labeled stars, which lets the outcome leak into the test. They now come from the league median, and the gates are tested out of sample.
- A team "value composite" was dropped: it was validated against WAR, which already contains baserunning and fielding, and one component scored lost win probability as a positive.
- A minor-league chase rate that was built mostly from spring-training pitches was removed, and minor-league lines were regenerated from official totals.

## Reproducing the analysis

```bash
git clone https://github.com/wksprojects/yanks_analytics.git
cd yanks_analytics
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

pytest -q
jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb
```

The first run downloads seven seasons of Statcast data (about 100 MB per season as parquet) and caches it under `src/yanks_analytics/data/cache/`. Later runs read from the cache.

## Repository guide

| Path | Purpose |
| --- | --- |
| `src/yanks_analytics/features/season.py` | Season and plate-appearance-window hitter tables, wOBA, outcome labels |
| `src/yanks_analytics/features/pitch_level.py` | Pitch classification (zone, swing, whiff, pitch group) |
| `src/yanks_analytics/features/team.py` | Validated FanGraphs team batting and fielding merge |
| `src/yanks_analytics/data/` | Data fetching and caching, the curated cohort, official minor-league lines |
| `notebooks/` | The five analyses, executed |
| `outputs/figures/`, `outputs/data/` | Figures and tables written by the notebooks |
| `tests/` | Unit tests for metric definitions and data integrity |

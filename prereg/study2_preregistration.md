# Pre-registration, Study 2: weather phenomena across 28 exchanges

**Status:** FROZEN at the git commit that first adds this file. Changes after that go in
`prereg/deviations.md` with IDs S2-D1, S2-D2, ….

**What had been seen before freezing:** all Study 1 results (New York and Sydney: cloud, temperature,
SAD; see `results/`), and the fact that each Yahoo index listed in §2 exists with its date range and
share of zero-change days. **No return series for the 26 new exchanges has been regressed on
anything.** The Study 1 exchanges are excluded from the primary tests for this reason (§4).

---

## 1. Questions
1. Do cloud cover and other weather phenomena (sunshine, temperature, wind, rain, humidity,
   pressure) move same-day stock returns across a broad set of exchanges?
2. Does the Hirshleifer–Shumway (2003) international cloud effect hold out of sample, after their
   sample ended in 1997?
3. Does seasonal variation in returns follow the local season, which is reversed in the southern
   hemisphere, or the calendar?

## 2. Exchanges (fixed; `src/weather/data/exchanges.py` is authoritative)
**Rule:** every major exchange whose benchmark index has free daily Yahoo history starting no later
than 2006-01-01 with fewer than 5% zero-change days, plus New York and Sydney from Study 1. Tel Aviv
(16% zero-change days) and indices starting after 2006 are excluded.

| Region | Exchanges (index) |
|---|---|
| Europe (12) | London (^FTSE), Frankfurt (^GDAXI), Paris (^FCHI), Zurich (^SSMI), Amsterdam (^AEX), Brussels (^BFX), Madrid (^IBEX), Milan (FTSEMIB.MI), Vienna (^ATX), Athens (GD.AT), Dublin (^ISEQ), Istanbul (XU100.IS) |
| Asia (9) | Tokyo (^N225), Hong Kong (^HSI), Singapore (^STI), Seoul (^KS11), Taipei (^TWII), Shanghai (000001.SS), Mumbai (^BSESN), Jakarta (^JKSE), Kuala Lumpur (^KLSE) |
| Americas (4) | Toronto (^GSPTSE), Mexico City (^MXX), São Paulo (^BVSP), Buenos Aires (^MERV) |
| Oceania (1) | Wellington (^NZ50) |
| Study 1 (2, secondary only) | New York (Ken French Mkt), Sydney (All Ords + dividends) |

- **Primary sample:** the 26 new exchanges, from each index's first date through 2026-08-31.
- **Southern hemisphere:** São Paulo, Buenos Aires, Wellington and Jakarta (6°S, near-equatorial),
  plus Sydney in the secondary sample.

## 3. Variables

### 3.1 Returns
- `r_it` = 100 × log price change of the index (price indices; dividends are ignored). A dividend
  add-back is not available for most indices, and deseasonalised weather is nearly orthogonal to
  dividend seasonality. This matters only for S9 and is a stated limitation.
- **Data-quality filters, applied before any regression:** drop exchange-days with |r| > 20%, and
  drop days with an exactly zero return (stale prices).
- **Dependent variable (primary):** volatility-scaled return `y_it = r_it / σ_i,t−1`, where σ is the
  standard deviation of r over the previous 60 trading days of that exchange (at least 40 required).
  β is therefore in units of a daily return SD. We also report β × median σ in basis points.
  (Scaling stops high-volatility emerging markets from dominating the pooled estimate.)
- **Controls:** exchange fixed effects; day-of-week dummies; pre- and post-holiday dummies (skipped
  weekdays); turn-of-year (last trading day of December and first 5 of January); two lags of y; and
  the most recent US market return dated strictly before t (Ken French Mkt, scaled by its own σ).

### 3.2 Weather: ERA5 via the Copernicus CDS, same processing for every city
Each variable is aggregated over 06:00–16:00 local time (for ERA5 accumulations, the hours ending
07:00–16:00):

| Name | Definition | Anomaly |
|---|---|---|
| CLOUD | mean total cloud cover | z-score |
| SUN | surface solar radiation, sum | z-score |
| TEMP | mean 2 m temperature | z-score |
| WIND | mean 10 m wind speed | z-score |
| HUMID | mean relative humidity (from temperature and dew point) | z-score |
| PRESS | mean sea-level pressure | z-score |
| RAIN | 1 if precipitation ≥ 1 mm | indicator minus its climatological frequency (not scaled) |

- **z-score:** as in Study 1. `(X_t − m_t)/s_t`, with m and s from the same ISO week in the previous
  30 years, strictly before t, requiring at least 5 years. ERA5 starts in 1950, so every exchange has
  a climatology from 1955.
- **SAD / FALL:** the KKL (2003) definitions at each exchange's latitude and local season.
  `SAD_CAL`: the same function evaluated at |latitude| with the northern-hemisphere calendar (equal to
  SAD for northern exchanges).

## 4. Primary hypotheses (Holm family of 9; pooled over the 26 new exchanges)
| ID | Variable | Prediction | Test |
|---|---|---|---|
| S1 | CLOUD, full sample | β < 0 | one-sided |
| S2 | CLOUD, 1998-01-01 onward (after the HS sample) | β < 0 | one-sided |
| S3 | SUN | β > 0 | one-sided |
| S4 | TEMP | β < 0 (Cao–Wei) | one-sided |
| S5 | WIND | β < 0 (Keef–Roush) | one-sided |
| S6 | RAIN | β < 0 | one-sided |
| S7 | HUMID | β ≠ 0 | two-sided |
| S8 | PRESS | β ≠ 0 | two-sided |
| S9 | SAD (local season), with SAD_CAL, FALL and FALL_CAL also included | β_SAD > 0 | one-sided |

Each of S1–S8 is a separate regression with one weather variable plus the controls. In S9, SAD and
SAD_CAL are identified only by the southern-hemisphere exchanges; with just 3–4 such exchanges the
test has low power, and we will say so.

## 5. Estimation and inference
- Pooled OLS with exchange fixed effects. **Driscoll–Kraay** standard errors (Newey–West on
  date-summed scores, 5 lags) allow for correlation across exchanges on the same day and for serial
  correlation.
- **Decision rule, identical to Study 1:** SUPPORTED if the Holm-adjusted p < 0.05 (family of 9) **and**
  the placebo percentile is in the predicted tail (5% one-sided; 2.5% in either tail for two-sided
  tests). INCONCLUSIVE if only one holds; NOT SUPPORTED otherwise. S9 is judged on Holm alone (as
  D4 in Study 1).
- **Placebo assignment:** 200 draws (seed 20260928). In each draw, every exchange gets the weather
  of a city drawn at random from the 100 Study 1 placebo cities, excluding exchange cities and any
  city within 1,000 km of that exchange. The pooled β is re-estimated each time, and the percentile
  is the share of draws at least as extreme as the real β.

## 6. Power (before seeing results)
About 26 × 7,500 ≈ 195,000 exchange-days. Returns are correlated across exchanges, but weather
anomalies in cities more than 1,000 km apart are mostly independent, so the effective N for β is
large. With unit-variance y, SE(β) ≈ 0.003 SD, giving an MDE (80% power, one-sided 5%) of about
0.8% of a daily SD per 1-SD weather shock, roughly 1 bp for a 1.2% daily-volatility index. S9 has far
less power.

## 7. Secondary / exploratory (reported; not in the Holm family)
- The 28-exchange version of S1–S9 (adds New York and Sydney).
- Per-exchange β for every phenomenon, with a Benjamini–Hochberg FDR at 10% across all
  exchange × variable tests.
- Pre/post-2003 splits for every phenomenon.
- A joint model with all seven anomalies together.
- Extreme events: storm days (gust above the trailing 30-year 99th percentile for that ISO week) and
  heat days (TEMP z > 2).
- Splits by hemisphere and by developed vs emerging markets (MSCI classification as of 2026).
- A Halloween dummy horse race.
- Absolute scaled return |y| (volatility) as the outcome.
- Raw (unscaled) returns.

## 8. Deviations
Logged in `prereg/deviations.md` with IDs S2-D1, S2-D2, ….

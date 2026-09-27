# Pre-registration: Does the weather still move markets?
## A two-hemisphere, post-publication test of weather and seasonal-mood effects in US and Australian equities

**Status:** FROZEN at the git commit that first adds this file. Any later change goes in the
deviations table (§10), with date, reason, and whether it was made before or after seeing results.

**Written before any regression on data after 2003-06-30.** Before freezing, the only
results the authors had seen were the published papers themselves.

---

## 1. Research questions
1. Do the classic weather/mood effects on daily index returns (cloud cover, temperature,
   seasonal affective disorder / daylight) exist in the US and Australia?
2. Do they survive after publication (July 2003 – August 2026)?
3. Does seasonal variation in returns follow the **season** (opposite in the two hemispheres)
   or the **calendar** (the same in both)?
4. Does exchange-city weather matter less once trading moves off the physical floor?

## 2. Samples
| Market | Returns | Start | End (frozen) |
|---|---|---|---|
| US | Ken French daily `Mkt` (= Mkt-RF + RF, CRSP VW, total return) | first day with ≥ 5 years of trailing weather climatology (weather from 1948 → returns from ~1953) | 2026-08-31 (or last available Ken French date, if earlier) |
| AU | S&P/ASX All Ordinaries `^AORD` (Yahoo), made total-return (§3) | 1984-08-03 | 2026-08-31 |

- **Pre-publication period:** start → 2003-06-30 (the month Hirshleifer–Shumway appeared in *JF*).
- **Post-publication period:** 2003-07-01 → end.
- Returns are log returns in percent. Days with a missing weather value for that market are dropped.

## 3. Variables

### 3.1 Returns
- US: `r_US,t = ln(1 + (MktRF_t + RF_t)/100) × 100`.
- AU: `r_AU,t = ln(P_t/P_{t−1}) × 100 + d_t`. Here `d_t` is the daily dividend add-back: the RBA table F7
  monthly ASX dividend yield ÷ number of trading days that month. If Yahoo has a usable S&P/ASX 200
  total-return index covering ≥ 1993–2026, use it as a robustness series.
- **Controls:** day-of-week dummies; a turn-of-year dummy (last trading day of Dec + first 5 of Jan);
  pre-holiday and post-holiday dummies (exchange calendar); a tax-year-end dummy (US: last 5 trading days of
  Dec; AU: last 5 trading days of June); two lags of own return. **AU only:** the US return on the
  most recent US session that closed before the ASX open (`r_US` of calendar date t−1 or earlier).

### 3.2 Weather (primary source: NOAA ISD-Lite hourly)
| City | Primary station | Fallback |
|---|---|---|
| New York | LaGuardia 725030-14732 | Central Park 725053-94728, then JFK 744860-94789 |
| Sydney | Sydney Airport 947670 | Sydney Observatory Hill (BoM 066062) for temperature |

- **CLOUD:** mean ISD total sky-cover code (oktas, 0–8; codes 9/10 and "obscured" → missing) over the
  hourly observations from 06:00 to 16:00 local standard/daylight time on day t. A day needs ≥ 4 valid
  hourly observations, otherwise missing. (This follows Hirshleifer–Shumway's 6am–4pm window.)
- **TEMP:** mean air temperature (°C) over the same window and with the same validity rule.
- **RAIN** (secondary, not a primary test): 06:00–16:00 precipitation > 0 indicator.
- **Deseasonalisation (primary):** for variable X on day t, the anomaly is
  `X*_t = (X_t − m_t)/s_t`, where `m_t` and `s_t` are the mean and SD of X over all days in the same
  ISO week in the **previous 30 calendar years, strictly before t** (at least 5 years required).
  This has no look-ahead.
- **Deseasonalisation (replication only):** a full-sample ISO-week mean, as in HS 2003.

### 3.3 Seasonal-mood variables (Kamstra–Kramer–Levi 2003 AER specification)
- Night length `H_t` (hours) computed astronomically for the exchange-city latitude (NYC 40.71°N,
  Sydney 33.87°S). We use the KKL formula from solar declination, not an external table.
- `SAD_t = H_t − 12` during that hemisphere's autumn and winter (north: 21 Sep – 20 Mar; south:
  21 Mar – 20 Sep), else 0.
- `FALL_t = 1` during that hemisphere's autumn (north: 21 Sep – 20 Dec; south: 21 Mar – 20 Jun).
- KKL predict **β_SAD > 0 and β_FALL < 0**.
- **Calendar-aligned counterparts for AU** (used in H3): `SAD^NYC_t` and `FALL^NYC_t`, the New York
  series applied to Australian dates, plus `HALLOWEEN_t = 1` for Nov–Apr.

## 4. Hypotheses (primary family, 9 tests)
All tests are one-sided, in the direction the original literature predicts.

| ID | Market | Model | Prediction |
|---|---|---|---|
| H1-US | US | r on CLOUD* + controls, full sample | β_CLOUD < 0 |
| H1-AU | AU | same | β_CLOUD < 0 |
| H2-US | US | r on CLOUD*·PRE + CLOUD*·POST + controls | β_POST < 0 (the effect survives publication) |
| H2-AU | AU | same | β_POST < 0 |
| H3-AU | AU | r on SAD^SYD + FALL^SYD + SAD^NYC + FALL^NYC + controls | β(SAD^SYD) > 0, the season-aligned effect |
| H4-US | US | r on TEMP* + controls | β_TEMP < 0 |
| H4-AU | AU | same | β_TEMP < 0 |
| H5-US | US | r on CLOUD* + CLOUD*·HYBRID + controls, HYBRID = 1 from 2007-01-24 | β_interaction > 0 (the effect weakens) |
| H6-US | US | (Size decile 1 − decile 10 daily return) on CLOUD* + controls | β_CLOUD < 0 |

**Secondary / exploratory (reported, not in the Holm family):** the US SAD/FALL replication in the full
sample and post-2003; the AU Halloween-dummy horse race; CLOUD·COVID-floor-closure (from 2020-03-23)
interaction; AU small-minus-large (`^AXSO` − `^AFLI`, or the closest available pair); RAIN; the full-sample
H2 break at the HS working-paper date (2001-01-01); ERA5 (Open-Meteo) weather in place of ISD;
Melbourne and Chicago weather; industry portfolios (energy, utilities, agriculture, retail) as a
physical-channel check; GARCH(1,1) and logit up/down specifications; a cloud-timed trading
strategy net of costs.

## 5. Estimation and inference
- OLS with Newey–West HAC standard errors, lag = 5 trading days.
- **Decision rule:** a primary hypothesis is **SUPPORTED** only if both hold:
  1. its one-sided HAC p-value survives the **Holm** correction at family-wise α = 0.05 across the 9
     primary tests; and
  2. the **placebo percentile** (§6) is in the predicted 5% tail.

  If only (1) or only (2) holds, it is **INCONCLUSIVE**; otherwise **NOT SUPPORTED**. Romano–Wolf stepdown
  (stationary bootstrap, mean block 10 days, 5,000 reps, seed 20260927) is reported as robustness.

## 6. Placebo inference
- **(a) Placebo cities:** the fixed list of 100 cities in Appendix A (national capitals and large cities
  more than 1,000 km from both New York and Sydney). For each, CLOUD and TEMP come from Open-Meteo ERA5
  hourly data, with the same 06:00–16:00 local window and the same deseasonalisation. The real city is
  re-estimated with ERA5 too, so the comparison is like for like. Percentile = share of placebo β at or
  beyond the real β in the predicted direction.
- **(b) Year-shifted weather:** replace W_t with the same calendar day's anomaly from year t−k, for
  k = 1…30 (skipping missing years). Report where the true β falls in that distribution.

## 7. Power (computed before seeing results)
With daily σ(r) ≈ 1.0% and a unit-variance regressor, SE(β) ≈ σ/√N.
- Post-2003, N ≈ 5,800 → SE ≈ 1.3 bp. The minimum detectable effect (80% power, one-sided 5%) is about
  2.5 × 1.3 ≈ **3.3 bp per 1 SD**; at the Holm-adjusted threshold it is about **4 bp**.
- Full US sample, N ≈ 18,000 → MDE ≈ 2 bp.

Published magnitudes (HS 2003, NYC) are of this order, so a post-publication null is informative
only if its confidence interval excludes effects of about 3–4 bp. We will report CIs, not just p-values.

## 8. Replication gate (runs before any post-2003 estimate)
- **HS 2003 NYC** window 1982-01-01 → 1997-12-31, full-sample weekly deseasonalisation, logit of
  up/down on CLOUD*. Pass = same sign as HS (negative) with one-sided p < 0.10.
- **KKL 2003 US** window 1928 → 2000, with Ken French returns, SAD + FALL + their controls. Pass = β_SAD > 0
  and β_FALL < 0 with one-sided p < 0.10.

If the gate fails, we find the cause (data source, window, coding) and document it before
continuing. The primary tests in §4 go ahead either way, and the gate outcome is reported.

## 9. Data-quality rules (fixed in advance)
- Station moves or code changes are documented. We do not splice series, except for the fallback order
  in §3.2, applied day by day when the primary station is missing.
- Returns larger than ±25% in a day are checked against a second source. They are kept if genuine
  (e.g. 1987-10-19).
- The AU price index is checked against `^AXJO` for overlapping dates (correlation of daily returns
  > 0.98 expected).

## 10. Deviations log
| Date | Section | Change | Before/after seeing results | Reason |
|---|---|---|---|---|
| | | | | |

---

## Appendix A: Placebo cities (fixed list, 100)
Coordinates are rounded to 0.01°; the time zone is the IANA zone used for the 06:00–16:00 window.
The list is kept in machine-readable form in `src/weather/data/placebo_cities.py`. That file is
authoritative, and the list may not be edited after freezing.

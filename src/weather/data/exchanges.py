"""Study 2 exchange list (fixed in prereg/study2_preregistration.md). Do not edit after freezing.

Rule: every major exchange whose benchmark index has free daily history on Yahoo starting no
later than 2006-01-01 with fewer than 5% zero-change days, plus New York and Sydney from Study 1.
Tuples: (city, lat, lon, IANA tz, return source).
"""

from __future__ import annotations

EXCHANGES: list[tuple[str, float, float, str, str]] = [
    ("New York", 40.71, -74.01, "America/New_York", "FRENCH_MKT"),
    ("Sydney", -33.87, 151.21, "Australia/Sydney", "AORD_DIV"),
    ("London", 51.51, -0.09, "Europe/London", "^FTSE"),
    ("Frankfurt", 50.11, 8.68, "Europe/Berlin", "^GDAXI"),
    ("Paris", 48.87, 2.34, "Europe/Paris", "^FCHI"),
    ("Zurich", 47.37, 8.54, "Europe/Zurich", "^SSMI"),
    ("Amsterdam", 52.37, 4.89, "Europe/Amsterdam", "^AEX"),
    ("Brussels", 50.85, 4.35, "Europe/Brussels", "^BFX"),
    ("Madrid", 40.42, -3.70, "Europe/Madrid", "^IBEX"),
    ("Milan", 45.46, 9.19, "Europe/Rome", "FTSEMIB.MI"),
    ("Vienna", 48.21, 16.37, "Europe/Vienna", "^ATX"),
    ("Athens", 37.98, 23.73, "Europe/Athens", "GD.AT"),
    ("Dublin", 53.35, -6.26, "Europe/Dublin", "^ISEQ"),
    ("Istanbul", 41.01, 28.98, "Europe/Istanbul", "XU100.IS"),
    ("Tokyo", 35.68, 139.77, "Asia/Tokyo", "^N225"),
    ("Hong Kong", 22.28, 114.16, "Asia/Hong_Kong", "^HSI"),
    ("Singapore", 1.28, 103.85, "Asia/Singapore", "^STI"),
    ("Seoul", 37.57, 126.98, "Asia/Seoul", "^KS11"),
    ("Taipei", 25.03, 121.56, "Asia/Taipei", "^TWII"),
    ("Shanghai", 31.23, 121.47, "Asia/Shanghai", "000001.SS"),
    ("Mumbai", 18.93, 72.83, "Asia/Kolkata", "^BSESN"),
    ("Jakarta", -6.21, 106.85, "Asia/Jakarta", "^JKSE"),
    ("Kuala Lumpur", 3.14, 101.69, "Asia/Kuala_Lumpur", "^KLSE"),
    ("Toronto", 43.65, -79.38, "America/Toronto", "^GSPTSE"),
    ("Mexico City", 19.43, -99.13, "America/Mexico_City", "^MXX"),
    ("Sao Paulo", -23.55, -46.63, "America/Sao_Paulo", "^BVSP"),
    ("Buenos Aires", -34.60, -58.38, "America/Argentina/Buenos_Aires", "^MERV"),
    ("Wellington", -41.29, 174.78, "Pacific/Auckland", "^NZ50"),
]

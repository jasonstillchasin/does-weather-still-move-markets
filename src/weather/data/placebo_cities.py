"""Fixed placebo-city list (pre-registration Appendix A). Do not edit after freezing.

Rule: 100 national capitals / large cities outside the US and Australia, each more than
1,000 km from both New York and Sydney. Tuples are (name, lat, lon, IANA time zone).
"""

from __future__ import annotations

PLACEBO_CITIES: list[tuple[str, float, float, str]] = [
    # Europe (30)
    ("London", 51.51, -0.13, "Europe/London"),
    ("Paris", 48.86, 2.35, "Europe/Paris"),
    ("Berlin", 52.52, 13.40, "Europe/Berlin"),
    ("Madrid", 40.42, -3.70, "Europe/Madrid"),
    ("Rome", 41.90, 12.50, "Europe/Rome"),
    ("Lisbon", 38.72, -9.14, "Europe/Lisbon"),
    ("Dublin", 53.35, -6.26, "Europe/Dublin"),
    ("Amsterdam", 52.37, 4.90, "Europe/Amsterdam"),
    ("Brussels", 50.85, 4.35, "Europe/Brussels"),
    ("Vienna", 48.21, 16.37, "Europe/Vienna"),
    ("Warsaw", 52.23, 21.01, "Europe/Warsaw"),
    ("Prague", 50.08, 14.44, "Europe/Prague"),
    ("Budapest", 47.50, 19.04, "Europe/Budapest"),
    ("Stockholm", 59.33, 18.07, "Europe/Stockholm"),
    ("Oslo", 59.91, 10.75, "Europe/Oslo"),
    ("Copenhagen", 55.68, 12.57, "Europe/Copenhagen"),
    ("Helsinki", 60.17, 24.94, "Europe/Helsinki"),
    ("Athens", 37.98, 23.73, "Europe/Athens"),
    ("Bucharest", 44.43, 26.10, "Europe/Bucharest"),
    ("Sofia", 42.70, 23.32, "Europe/Sofia"),
    ("Belgrade", 44.79, 20.45, "Europe/Belgrade"),
    ("Zagreb", 45.81, 15.98, "Europe/Zagreb"),
    ("Kyiv", 50.45, 30.52, "Europe/Kyiv"),
    ("Moscow", 55.76, 37.62, "Europe/Moscow"),
    ("Istanbul", 41.01, 28.98, "Europe/Istanbul"),
    ("Reykjavik", 64.15, -21.94, "Atlantic/Reykjavik"),
    ("Bern", 46.95, 7.45, "Europe/Zurich"),
    ("Riga", 56.95, 24.11, "Europe/Riga"),
    ("Vilnius", 54.69, 25.28, "Europe/Vilnius"),
    ("Minsk", 53.90, 27.57, "Europe/Minsk"),
    # Middle East and Africa (25)
    ("Cairo", 30.04, 31.24, "Africa/Cairo"),
    ("Tehran", 35.69, 51.39, "Asia/Tehran"),
    ("Riyadh", 24.71, 46.68, "Asia/Riyadh"),
    ("Baghdad", 33.31, 44.36, "Asia/Baghdad"),
    ("Dubai", 25.20, 55.27, "Asia/Dubai"),
    ("Amman", 31.95, 35.93, "Asia/Amman"),
    ("Tel Aviv", 32.09, 34.78, "Asia/Jerusalem"),
    ("Lagos", 6.52, 3.38, "Africa/Lagos"),
    ("Nairobi", -1.29, 36.82, "Africa/Nairobi"),
    ("Addis Ababa", 9.03, 38.74, "Africa/Addis_Ababa"),
    ("Johannesburg", -26.20, 28.05, "Africa/Johannesburg"),
    ("Cape Town", -33.92, 18.42, "Africa/Johannesburg"),
    ("Casablanca", 33.57, -7.59, "Africa/Casablanca"),
    ("Algiers", 36.75, 3.06, "Africa/Algiers"),
    ("Tunis", 36.81, 10.18, "Africa/Tunis"),
    ("Accra", 5.60, -0.19, "Africa/Accra"),
    ("Dakar", 14.72, -17.47, "Africa/Dakar"),
    ("Kinshasa", -4.44, 15.27, "Africa/Kinshasa"),
    ("Luanda", -8.84, 13.23, "Africa/Luanda"),
    ("Khartoum", 15.50, 32.56, "Africa/Khartoum"),
    ("Dar es Salaam", -6.79, 39.21, "Africa/Dar_es_Salaam"),
    ("Kampala", 0.35, 32.58, "Africa/Kampala"),
    ("Harare", -17.83, 31.05, "Africa/Harare"),
    ("Antananarivo", -18.88, 47.51, "Indian/Antananarivo"),
    ("Abidjan", 5.36, -4.01, "Africa/Abidjan"),
    # Asia (25)
    ("Tokyo", 35.68, 139.69, "Asia/Tokyo"),
    ("Seoul", 37.57, 126.98, "Asia/Seoul"),
    ("Beijing", 39.90, 116.41, "Asia/Shanghai"),
    ("Shanghai", 31.23, 121.47, "Asia/Shanghai"),
    ("Hong Kong", 22.32, 114.17, "Asia/Hong_Kong"),
    ("Taipei", 25.03, 121.57, "Asia/Taipei"),
    ("Manila", 14.60, 120.98, "Asia/Manila"),
    ("Bangkok", 13.76, 100.50, "Asia/Bangkok"),
    ("Hanoi", 21.03, 105.85, "Asia/Bangkok"),
    ("Jakarta", -6.21, 106.85, "Asia/Jakarta"),
    ("Kuala Lumpur", 3.14, 101.69, "Asia/Kuala_Lumpur"),
    ("Singapore", 1.35, 103.82, "Asia/Singapore"),
    ("Delhi", 28.61, 77.21, "Asia/Kolkata"),
    ("Mumbai", 19.08, 72.88, "Asia/Kolkata"),
    ("Dhaka", 23.81, 90.41, "Asia/Dhaka"),
    ("Karachi", 24.86, 67.01, "Asia/Karachi"),
    ("Kabul", 34.56, 69.21, "Asia/Kabul"),
    ("Tashkent", 41.30, 69.24, "Asia/Tashkent"),
    ("Almaty", 43.24, 76.89, "Asia/Almaty"),
    ("Ulaanbaatar", 47.89, 106.91, "Asia/Ulaanbaatar"),
    ("Kathmandu", 27.72, 85.32, "Asia/Kathmandu"),
    ("Colombo", 6.93, 79.86, "Asia/Colombo"),
    ("Yangon", 16.84, 96.17, "Asia/Yangon"),
    ("Phnom Penh", 11.56, 104.93, "Asia/Phnom_Penh"),
    ("Osaka", 34.69, 135.50, "Asia/Tokyo"),
    # Americas outside the US (20)
    ("Mexico City", 19.43, -99.13, "America/Mexico_City"),
    ("Guatemala City", 14.63, -90.51, "America/Guatemala"),
    ("Havana", 23.11, -82.37, "America/Havana"),
    ("Bogota", 4.71, -74.07, "America/Bogota"),
    ("Caracas", 10.48, -66.90, "America/Caracas"),
    ("Lima", -12.05, -77.04, "America/Lima"),
    ("Quito", -0.18, -78.47, "America/Guayaquil"),
    ("Santiago", -33.45, -70.67, "America/Santiago"),
    ("Buenos Aires", -34.60, -58.38, "America/Argentina/Buenos_Aires"),
    ("Montevideo", -34.90, -56.16, "America/Montevideo"),
    ("Sao Paulo", -23.55, -46.63, "America/Sao_Paulo"),
    ("Rio de Janeiro", -22.91, -43.17, "America/Sao_Paulo"),
    ("Brasilia", -15.79, -47.88, "America/Sao_Paulo"),
    ("La Paz", -16.50, -68.15, "America/La_Paz"),
    ("Asuncion", -25.26, -57.58, "America/Asuncion"),
    ("Panama City", 8.98, -79.52, "America/Panama"),
    ("San Jose CR", 9.93, -84.08, "America/Costa_Rica"),
    ("Santo Domingo", 18.49, -69.93, "America/Santo_Domingo"),
    ("Vancouver", 49.28, -123.12, "America/Vancouver"),
    ("Winnipeg", 49.90, -97.14, "America/Winnipeg"),
]

# Exchange cities and robustness cities (not placebos).
CITIES: dict[str, tuple[float, float, str]] = {
    "NYC": (40.71, -74.01, "America/New_York"),
    "SYD": (-33.87, 151.21, "Australia/Sydney"),
    "MEL": (-37.81, 144.96, "Australia/Melbourne"),
    "CHI": (41.88, -87.63, "America/Chicago"),
}


def km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres."""
    import math

    p1, p2 = math.radians(lat1), math.radians(lat2)
    c = (math.sin(p1) * math.sin(p2)
         + math.cos(p1) * math.cos(p2) * math.cos(math.radians(lon2 - lon1)))
    return 6371 * math.acos(min(1.0, max(-1.0, c)))

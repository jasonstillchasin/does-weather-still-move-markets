"""Fetch full-variable ERA5 series for Study 2: 28 exchanges plus the 100 placebo cities."""

from __future__ import annotations

import logging

from weather.data import era5_full
from weather.data.exchanges import EXCHANGES
from weather.data.placebo_cities import PLACEBO_CITIES

logging.basicConfig(level=logging.WARNING)


def main() -> None:
    todo = [(c, lat, lon, tz) for c, lat, lon, tz, _ in EXCHANGES]
    names = {c[0] for c in todo}
    todo += [c for c in PLACEBO_CITIES if c[0] not in names]
    todo = [c for c in todo if not era5_full.path_for(c[0]).exists()]
    print(f"{len(todo)} cities to fetch", flush=True)
    for c in todo:  # one at a time: CDS limits queued requests per user
        try:
            d = era5_full.fetch(*c)
            print(c[0], len(d), flush=True)
        except Exception as e:
            print(c[0], "FAILED", repr(e)[:200], flush=True)


if __name__ == "__main__":
    main()

"""Fetch ERA5 point series for all 104 cities from the Copernicus CDS (deviation D5)."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from weather.data import era5_cds
from weather.data.placebo_cities import CITIES, PLACEBO_CITIES

logging.basicConfig(level=logging.WARNING)
# CDS limits queued requests per user; one at a time avoids rejections.
WORKERS = 1


def main() -> None:
    todo = [(k, *v) for k, v in CITIES.items()] + list(PLACEBO_CITIES)
    todo = [c for c in todo if not era5_cds.path_for(c[0]).exists()]
    print(f"{len(todo)} cities to fetch", flush=True)
    with ThreadPoolExecutor(WORKERS) as ex:
        futs = {ex.submit(era5_cds.fetch, *c): c[0] for c in todo}
        for f in as_completed(futs):
            try:
                print(futs[f], len(f.result()), flush=True)
            except Exception as e:  # keep going; rerun picks up failures
                print(futs[f], "FAILED", repr(e)[:200], flush=True)


if __name__ == "__main__":
    main()

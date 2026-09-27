"""HTTP GET with retries, and the project cache root."""

from __future__ import annotations

import logging
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[3]
CACHE = ROOT / "data" / "cache"
log = logging.getLogger(__name__)
HEADERS = {"User-Agent": "weather-markets-research/0.1 (academic replication package)"}


def get(url: str, params=None, allow_404: bool = False, tries: int = 5) -> bytes | None:
    for attempt in range(tries):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=120)
            if r.status_code == 404 and allow_404:
                return None
            if r.status_code == 429 or r.status_code >= 500:
                raise requests.HTTPError(f"{r.status_code}")
            r.raise_for_status()
            return r.content
        except (requests.RequestException, requests.HTTPError) as e:
            wait = 2**attempt
            log.warning("GET %s failed (%s); retry in %ss", url, e, wait)
            time.sleep(wait)
    raise RuntimeError(f"GET failed after {tries} tries: {url}")

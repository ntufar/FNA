import time
from typing import Optional, Dict, Any

import requests

_USER_AGENT = "FNA Platform (admin@fna.local)"
_SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# simple in-process cache
_cache: Dict[str, Any] = {
    "fetched_at": 0.0,
    "data": None,
}
_CACHE_TTL_SECONDS = 60 * 60  # 1 hour

def _load_sec_tickers() -> Optional[Dict[str, Any]]:
    now = time.time()
    if _cache["data"] is not None and (now - _cache["fetched_at"]) < _CACHE_TTL_SECONDS:
        return _cache["data"]
    try:
        resp = requests.get(_SEC_TICKERS_URL, headers={"User-Agent": _USER_AGENT}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        _cache["data"] = data
        _cache["fetched_at"] = now
        return data
    except Exception:
        return _cache["data"]  # return stale if available


def get_official_name_from_ticker(ticker: str) -> Optional[str]:
    """Return the official company name (SEC 'title') for a given ticker.

    Args:
        ticker: Ticker symbol, case-insensitive.

    Returns:
        Official company name if found, else None.
    """
    if not ticker:
        return None
    t = ticker.strip().upper()
    data = _load_sec_tickers()
    if not isinstance(data, dict):
        return None
    try:
        for entry in data.values():
            if isinstance(entry, dict) and entry.get("ticker") == t:
                title = entry.get("title")
                if isinstance(title, str) and title.strip():
                    return title.strip()
    except Exception:
        return None
    return None

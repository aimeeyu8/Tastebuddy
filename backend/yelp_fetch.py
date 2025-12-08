# backend/yelp_fetch.py

import os
from functools import lru_cache
from typing import List, Dict, Any

import requests

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
BASE_URL = "https://serpapi.com/search.json"

if not SERPAPI_KEY:
    raise RuntimeError("SERPAPI_API_KEY is not set in the environment (SERPAPI_API_KEY).")


def _normalize_restaurant(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a Yelp organic_result into the internal restaurant format."""
    place_ids = raw.get("place_ids") or []
    categories = raw.get("categories") or []
    cat_titles = [c.get("title", "") for c in categories]

    return {
        # stable ID used by Yelp Place / Yelp Reviews APIs
        "id": place_ids[0] if place_ids else None,
        "place_ids": place_ids,

        "title": raw.get("title"),
        "link": raw.get("link"),
        "rating": raw.get("rating"),
        "reviews": raw.get("reviews"),
        "price": raw.get("price"),
        "neighborhoods": raw.get("neighborhoods"),
        "snippet": raw.get("snippet"),
        "thumbnail": raw.get("thumbnail"),

        # convenience field used elsewhere for cuisine matching
        "categories": cat_titles,
        "type": ", ".join(cat_titles) if cat_titles else None,
    }


@lru_cache(maxsize=128)
def _cached_search(find_desc: str, find_loc: str, start: int, sortby: str) -> Dict[str, Any]:
    """
    Cached wrapper around the Yelp Search API.
    Matches SerpAPI docs: engine=yelp, find_desc, find_loc, start, sortby. :contentReference[oaicite:1]{index=1}
    """
    params = {
        "engine": "yelp",
        "find_desc": find_desc,
        "find_loc": find_loc,
        "start": start,
        "sortby": sortby,      # recommended | rating | review_count :contentReference[oaicite:2]{index=2}
        "api_key": SERPAPI_KEY,
    }
    resp = requests.get(BASE_URL, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


def yelp_search(
    term: str,
    location: str = "New York, NY, USA",
    limit: int = 10,
    sortby: str = "recommended",
) -> List[Dict[str, Any]]:
    """
    High-level helper:
    - calls SerpAPI Yelp Search with engine=yelp
    - paginates via `start`
    - returns a list of normalized restaurant dicts
    """
    restaurants: List[Dict[str, Any]] = []
    start = 0

    while len(restaurants) < limit and start <= 50:
        data = _cached_search(term, location, start, sortby)
        organic = data.get("organic_results") or []  # per docs :contentReference[oaicite:3]{index=3}
        if not organic:
            break

        for r in organic:
            restaurants.append(_normalize_restaurant(r))
            if len(restaurants) >= limit:
                break

        start += len(organic)

    return restaurants

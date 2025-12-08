# backend/yelp_place_fetch.py

import os
from functools import lru_cache
from typing import Dict, Any, List

import requests

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
BASE_URL = "https://serpapi.com/search.json"

if not SERPAPI_KEY:
    raise RuntimeError("SERPAPI_API_KEY is not set in the environment (SERPAPI_API_KEY).")


# prevent caching issues
@lru_cache(maxsize=256)
# use yelp_place api from SERPAPI and get place_id
def _fetch_place_basic(place_id: str) -> Dict[str, Any]:
    params = {
        "engine": "yelp_place",
        "place_id": place_id,
        "api_key": SERPAPI_KEY,
    }
    resp = requests.get(BASE_URL, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


@lru_cache(maxsize=256)
# access full menu from yelp_place API
def _fetch_place_full_menu(place_id: str) -> Dict[str, Any]:
    params = {
        "engine": "yelp_place",
        "place_id": place_id,
        "full_menu": "true",
        "api_key": SERPAPI_KEY,
    }
    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


@lru_cache(maxsize=256)
# fetch reveiws from yelp_reviews API
def _fetch_reviews(place_id: str) -> Dict[str, Any]:
    """
    Hit the Yelp Reviews API:
    engine=yelp_reviews, place_id
    """
    params = {
        "engine": "yelp_reviews",
        "place_id": place_id,
        "api_key": SERPAPI_KEY,
    }
    try:
        resp = requests.get(BASE_URL, params=params, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}


# parsing
def extract_menu_texts(full_menu_data: Dict[str, Any]) -> List[str]:
    """
    This converts the menu json into strings that are scanned to see if they contain allergens
    """
    texts: List[str] = []

    # Menu location can exisit in differetne locations, try all
    fm = (
        full_menu_data.get("full_menu_results") or
        full_menu_data.get("menu") or
        full_menu_data.get("menus") or
        full_menu_data.get("structured_menu") or
        {}
    )

    # Normalize sections, some restaurants may also store items into the sections
    sections = fm.get("sections") or fm.get("items") or []

    for section in sections:
        items = section.get("items", [])
        for item in items:
            title = item.get("title")
            desc = item.get("description") or item.get("text")
            combined = " ".join(p for p in [title, desc] if p)
            if combined.strip():
                texts.append(combined.strip())

    return texts


def extract_review_texts(review_data: Dict[str, Any]) -> List[str]:
    """
    If restaurant has no menu, review highlights may still have key allergens mentioned, extract from reviews to get text list to check for allergens
    """
    reviews = review_data.get("reviews") or []
    texts = []
    for r in reviews:
        body = r.get("snippet") or r.get("body")
        if isinstance(body, str) and body.strip():
            texts.append(body.strip())
    return texts



# public entry point called b y allergen_filter.py

def fetch_full_menu(place_id: str) -> Dict[str, Any]:
    """
    Fetches the basic information and full menu, including a fallback to reviews if no menu is available
    Returns a dictionary always containing:

    {
      "place_id": str,
      "menu_texts": [...],     
      "meta": {
          "address": str|None,
          "price": str|None,
          "phone": str|None,
          "categories": [str, ...]
      }
    }
    """
    # fetch basic info and full menu
    basic = _fetch_place_basic(place_id)
    full_menu = _fetch_place_full_menu(place_id)

    # place data
    place_results = (
        basic.get("place_results") or
        full_menu.get("place_results") or
        {}
    )

    # categories used in ranking and llm descriptions
    categories = place_results.get("categories") or []
    cat_titles = [
        c.get("title", "")
        for c in categories
        if isinstance(c, dict)
    ]

    # extract menu item texts
    menu_texts = extract_menu_texts(full_menu)

    # If no menu → fallback to reviews
    if not menu_texts:
        review_data = _fetch_reviews(place_id)
        review_texts = extract_review_texts(review_data)
        menu_texts = review_texts  # may still be empty; allergen_filter handles it

    return {
        "place_id": place_id,
        "menu_texts": menu_texts,
        "meta": {
            "address": place_results.get("address"),
            "price": place_results.get("price"),
            "phone": place_results.get("phone"),
            "categories": cat_titles,
        },
    }

# used for debuggin purposes 
def clear_cache():
    _fetch_place_basic.cache_clear()
    _fetch_place_full_menu.cache_clear()
    _fetch_reviews.cache_clear()

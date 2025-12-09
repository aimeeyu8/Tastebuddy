# backend/allergen_filter.py
# allergen_filter filters out restaurants that have high risk of containing allergens that the user put
# pulls full menu from yelp usng SERPAPI's yelp places api, then counts how many menu items mention the allegen, if too many contain, then restaurant is left out

from typing import List, Dict, Any, Tuple
# access from yelp_place_fetch
from .yelp_place_fetch import fetch_full_menu

# setting a threshold so that if a restaurant menu has 30% items or more with allergen, then it will be flagged
ALLERGEN_THRESHOLD_DEFAULT = 0.3  

# make sure all allergens are lowercase and stripped
def _normalize_allergen_terms(allergies: List[str]) -> List[str]:
    return [a.strip().lower() for a in allergies if a.strip()]

def _extract_review_texts(restaurant: Dict[str, Any]) -> List[str]:
    """Fallback: extract allergen-relevant text from Yelp review highlights."""
    reviews = restaurant.get("review_highlights") or []
    texts = []

    for r in reviews:
        # Each review highlight may contain: "review" and/or "highlight"
        parts = []
        if "review" in r and isinstance(r["review"], str):
            parts.append(r["review"])
        if "highlight" in r and isinstance(r["highlight"], str):
            parts.append(r["highlight"])

        if parts:
            combined = " ".join(parts).strip()
            if combined:
                texts.append(combined)

    return texts

# main allergen filtering function, inputs a list of restaurants and allergies, returns safe restaurants and debug info
def filter_allergens(
    restaurants: List[Dict[str, Any]],
    allergies: List[str],
    threshold: float = ALLERGEN_THRESHOLD_DEFAULT,
) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """
    Strictness B:
      - Look at FULL MENU via Yelp Place API for each restaurant (if place_id exists).
      - Compute fraction of menu items that contain any allergen term.
      - If fraction >= threshold (default 0.3), classify restaurant as ALLERGENIC and drop it.
      - If there is no full_menu, we do NOT automatically drop the restaurant (we treat it
        as "unknown" and leave it, but we return debug info so the LLM can caveat it).

    Returns:
      safe_restaurants, allergen_debug

      allergen_debug[restaurant_key] = {
        "place_id": str|None,
        "menu_items": int,
        "allergen_hits": int,
        "fraction": float|None,
        "blocked": bool,
      }
    """
    # if user has no allergies, return all restaurants because we can skip filtering
    if not allergies:
        return restaurants, {}

    # normalize allregen terms
    allergens = _normalize_allergen_terms(allergies)

    safe: List[Dict[str, Any]] = []
    debug: Dict[str, Dict[str, Any]] = {}

    # loop through restaurants
    for r in restaurants:
        # extract place_id so we can access the full menu from /yelp places api
        place_ids = r.get("place_ids") or []
        place_id = place_ids[0] if place_ids else None

        total_items = 0
        hits = 0
        fraction = None
        blocked = False

        # fetch full menu if place_id exists
        if place_id:
            menu_data = fetch_full_menu(place_id)
            menu_texts = menu_data.get("menu_texts") or []
            total_items = len(menu_texts)
        if not menu_texts:
            menu_texts = _extract_review_texts(r)
        total_items = len(menu_texts)

        if total_items > 0:
            for text in menu_texts:
                t = text.lower()
                if any(a in t for a in allergens):
                    hits += 1
            fraction = hits / total_items
            blocked = fraction >= threshold

        # Keep the restaurant unless we are sure >= threshold of items contain allergen.
        if not blocked:
            safe.append(r)

        key = r.get("title") or place_id or "unknown"
        debug[key] = {
            "place_id": place_id,
            "menu_items": total_items,
            "allergen_hits": hits,
            "fraction": fraction,
            "blocked": blocked,
            "used_review_fallback": (not r.get("menu") and total_items > 0)
        }

    return safe, debug

# backend/ranking.py
# ranks restaurants based on multiple criteria including yelp rating, review count, cuisine match, price match, and allergen friendliness

import math
from typing import List, Dict, Any, Optional

# inputs restaurants, prefs, allergen debug, and outputs list of restaurants ranked by score
def rank_restaurants(
    restaurants: List[Dict[str, Any]],
    prefs: Dict[str, Any],
    allergen_debug: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Multi-criteria ranking that leverages Yelp data:

      - Yelp Rating (0–5)           → 40%
      - log(review_count)           → 20%
      - Cuisine match               → 15%
      - Price match                 → 15%
      - Allergen friendliness       → 10% (1 - fraction of menu items with allergen; if unknown → 0.7)

    `allergen_debug` is the dict returned by filter_allergens(...).
    """
    # ensures cuisine is lowercase and a list for matching
    cuisines = prefs.get("cuisine") or []
    if isinstance(cuisines, str):
        cuisines = [cuisines]
    cuisines = [c.lower() for c in cuisines]

    # get prices
    price_pref = prefs.get("price") or "1,2,3,4"
    price_levels = [int(p) for p in price_pref.split(",") if p.strip().isdigit()]
    price_levels = [p for p in price_levels if 1 <= p <= 4] or [1, 2, 3, 4]

    # evaluates each restaurant and computes a score from 0 to 1
    def score_restaurant(r: Dict[str, Any]) -> float:
        # yelp rating converted to 0-1 scale, worth 15% weight
        rating_raw = r.get("rating") or 0
        try:
            rating = float(rating_raw)
        except (TypeError, ValueError):
            rating = 0.0
        rating_score = max(0.0, min(1.0, rating / 5.0))

        # Review count (0–1) using log scale, worth 10% weight
        reviews_raw = r.get("reviews") or 0
        try:
            reviews = float(reviews_raw)
        except (TypeError, ValueError):
            reviews = 0.0
        review_score = math.log1p(reviews) / math.log1p(1000.0)  # ~1 at 1000+ reviews

        # Cuisine match (0–1), worth 15% weight
        text = (
            " ".join(r.get("categories") or [])
            + " "
            + (r.get("title") or "")
        ).lower()
        cuisine_score = 1.0 if cuisines and any(c in text for c in cuisines) else 0.5 if cuisines else 0.5

        # Price match (0–1), worth 20% weight
        price_raw = r.get("price") or ""
        s = str(price_raw)
        dollar_count = s.count("$")
        if dollar_count:
            level = max(1, min(4, dollar_count))
        elif s.strip().isdigit():
            level = max(1, min(4, int(s.strip())))
        else:
            level = None

        if level is None:
            price_score = 0.6  # mildly neutral if unknown
        else:
            price_score = 1.0 if level in price_levels else 0.3

        # Allergen friendliness (0–1), worth 40% weight
        allergen_score = 0.7
        if allergen_debug is not None:
            key = r.get("title") or (r.get("place_ids") or [None])[0] or "unknown"
            info = allergen_debug.get(key)
            if info and info.get("fraction") is not None:
                fraction = info["fraction"]
                allergen_score = max(0.0, min(1.0, 1.0 - fraction))

        # Weighted sum
        total = (
            0.40 * allergen_score +
            0.20 * price_score +
            0.15 * cuisine_score +
            0.15 * rating_score +
            0.10 * review_score
        )
        return total

    scored = []
    for r in restaurants:
        s = score_restaurant(r)
        r_with_score = dict(r)
        r_with_score["_score"] = s
        scored.append(r_with_score)

    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored

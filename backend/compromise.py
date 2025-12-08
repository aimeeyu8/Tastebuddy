# backend/compromise.py

from typing import List, Tuple
import numpy as np

from .harmony_score import CUISINE_CATEGORIES, cosine_similarity


def restaurant_to_vec(r: dict) -> np.ndarray:
    """
    Turn restaurant attributes into a vector compatible with prefs_to_vec:
      [price_norm, allergy_count(=0), cuisine_one_hot...]
    """
    price_raw = r.get("price") or ""
    price_str = str(price_raw)

    # normalize restaurant price data from "$$", "3", etc.
    dollar_count = price_str.count("$")
    if dollar_count:
        price_level = float(max(0, min(dollar_count, 4)))
    else:
        s = price_str.strip()
        if s.isdigit():
            price_level = float(max(0, min(int(s), 4)))
        else:
            price_level = 0.0

    price_norm = price_level / 4.0 if price_level > 0 else 0.5

    # restaurants are treated as no allergy conflict by default
    allergy_count = 0.0

    cuisine_text = ((r.get("type") or "") + " " + (r.get("title") or "")).lower()
    cuisine_vec: List[float] = []
    for cat in CUISINE_CATEGORIES:
        cuisine_vec.append(1.0 if cat in cuisine_text else 0.0)

    return np.array([price_norm, allergy_count] + cuisine_vec, dtype="float32")


def best_compromise_restaurant(
    restaurants: List[dict],
    group_avg_prefs: np.ndarray,
) -> Tuple[dict, float]:
    """
    Select the restaurant whose vector is closest (cosine similarity) to
    the group's average preference vector.
    """
    if not restaurants:
        return None, 0.0

    best = None
    best_sim = -1.0

    for r in restaurants:
        vec = restaurant_to_vec(r)
        sim = cosine_similarity(vec, group_avg_prefs)
        if sim > best_sim:
            best_sim = sim
            best = r

    return best, float(best_sim)

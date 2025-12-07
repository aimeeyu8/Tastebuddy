# backend/harmony_score.py

from typing import Dict, List
from collections import Counter
import numpy as np

# ====== shared group preference state ======
# stores each user's latest preference dict
user_prefs: Dict[str, dict] = {}


# ====== your price normalization helper ======
def _normalize_price(raw_price) -> float:
    """Convert None / invalid → 0, clamp 0–4, scale to [0,1]."""
    try:
        val = int(raw_price) if raw_price is not None else 0
    except (ValueError, TypeError):
        val = 0
    val = max(0, min(val, 4))
    return val / 4.0


# ====== your original harmony logic ======
def compute_harmony_score(user_id: str, prefs: dict, group_prefs: Dict[str, dict]) -> float:
    """
    group_prefs: dict[user_id -> prefs] including this user
    returns a harmony score in [0, 1]
    """

    # 1. Separate user vs others
    others = {uid: p for uid, p in group_prefs.items() if uid != user_id}
    if not others:
        return 1.0  # only user → trivially harmonious

    user_cuisine = (prefs.get("cuisine") or "").lower().strip()
    user_price = _normalize_price(prefs.get("price_range") or prefs.get("price"))
    user_allergies = set((prefs.get("allergies") or []))

    # --- Cuisine alignment: how many others share this cuisine? ---
    other_cuisines = [
        (p.get("cuisine") or "").lower().strip()
        for p in others.values()
    ]
    cuisine_counts = Counter(other_cuisines)
    total_others = len(others)

    if not user_cuisine:
        cuisine_score = 0.5  # neutral if user didn't specify
    else:
        same_cuisine_count = cuisine_counts.get(user_cuisine, 0)
        cuisine_score = same_cuisine_count / total_others  # 0–1

    # --- Price alignment: compare with group average price ---
    other_prices = [
        _normalize_price(p.get("price_range") or p.get("price"))
        for p in others.values()
    ]
    group_avg_price = float(np.mean(other_prices)) if other_prices else user_price

    # difference in [0,1], then turn into a similarity (1 = same, 0 = very different)
    price_diff = abs(user_price - group_avg_price)
    price_score = max(0.0, 1.0 - price_diff)  # linear penalty

    # --- Allergy tension ---
    RISKY_CUISINES = {"thai", "sushi", "chinese", "indian", "middle eastern"}
    risky_fraction = (
        sum(1 for c in other_cuisines if c in RISKY_CUISINES) / total_others
        if total_others else 0.0
    )

    if not user_allergies:
        allergy_score = 1.0
    else:
        allergy_score = 1.0 - 0.6 * risky_fraction  # keep in [0.4, 1] roughly
        allergy_score = max(0.0, min(allergy_score, 1.0))

    # --- Combine: tuneable weights ---
    harmony = (
        0.4 * cuisine_score +
        0.4 * price_score +
        0.2 * allergy_score
    )

    return float(max(0.0, min(harmony, 1.0)))


def harmony_to_label(score: float) -> str:
    """
    Convert numeric harmony score into a natural-language descriptor.
    These labels never mention numbers, so the LLM won't reveal them.
    """
    if score >= 0.8:
        return "very aligned with the group"
    elif score >= 0.6:
        return "mostly aligned with the group"
    elif score >= 0.4:
        return "somewhat different from the group"
    else:
        return "quite different from the group"


# ====== wrapper used by main.py ======
def compute_harmony(user_id: str, prefs: dict) -> float:
    """
    This is the function imported in main.py.
    It:
    - updates the global user_prefs dict
    - builds group_prefs
    - calls your compute_harmony_score(...)
    """

    # update stored prefs for this user
    user_prefs[user_id] = prefs

    # group_prefs is just the current snapshot of everyone
    group_prefs = dict(user_prefs)

    score = compute_harmony_score(user_id, prefs, group_prefs)
    return float(score)


# ====== prefs_to_vec used for compromise / conflict resolution ======
def prefs_to_vec(prefs: dict) -> np.ndarray:
    """
    Convert prefs into a simple numeric vector for conflict / compromise logic.

    For now we only encode price into a 4-dim vector [p1, p2, p3, p4]
    from prefs["price"], which might look like '1', '2', '3,4', etc.
    """

    price_str = prefs.get("price") or "1,2,3,4"
    vec = np.zeros(4, dtype=float)

    parts: List[str] = [p.strip() for p in price_str.split(",") if p.strip()]
    for p in parts:
        if p in ["1", "2", "3", "4"]:
            idx = int(p) - 1
            vec[idx] += 1.0

    if vec.sum() == 0:
        vec[:] = 1.0

    vec = vec / vec.sum()
    return vec

# backend/harmony_score.py

from typing import Dict, List
from collections import Counter
import numpy as np

# shared group preference state
# stores each user's latest preference dict
user_prefs: Dict[str, dict] = {}
# one/multi-hot encoding
# shared cuisine space for vectors, basically each cuisine gets a one-hot dimension, a user gets 1.0 in dimensions matching their cusine while all other cuisines get 0.0
CUISINE_CATEGORIES: List[str] = [
    "sushi", "ramen", "thai", "italian", "mexican", "american", "indian", "vegan", "bbq", "pizza", "middle eastern", "mediterranean", "chinese", "japanese", "korean", "thai", "malaysian", "vietnamese", "spanish", "french", "peruvian", "soul food", "greek", "turkish", "lebanese", "ukranian", "lebanese", "moroccan", "egyptian", "ethiopian", "nigerian", "south african", "pakistani", "bangladeshi", "sri lankan", "nepali", "tibetan", "filipino", "indonesian", "singaporean", "australian", "southern", "brazilian", "argentinian", "columbian", "caribbean", "raw food", "fusion", "street food", "food truck"
]

# use cosine similarity(measures angle between 2 vectors) to compare preference vectors
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Safe cosine similarity in [0,1]."""
    if a.shape != b.shape:
        return 0.0
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    sim = float(np.dot(a, b) / (na * nb))
    # map from [-1,1] to [0,1]
    return 0.5 * (sim + 1.0)


# price normalization, converts to val between 0 and 1
def _normalize_price_raw(raw_price) -> float:
    """
    Convert '1', '2', '3,4', or None into a [0,1] scalar
    based on the average requested price level.
    """
    if raw_price is None:
        return 0.5

    s = str(raw_price)
    parts = [p.strip() for p in s.split(",") if p.strip()]
    levels = []
    for p in parts:
        if p.isdigit():
            val = max(1, min(4, int(p)))
            levels.append(val)

    if not levels:
        return 0.5

    avg = sum(levels) / len(levels)  # 1–4
    return avg / 4.0


# ====== harmony logic ======
def compute_harmony_score(user_id: str, prefs: dict, group_prefs: Dict[str, dict]) -> float:
    """
    group_prefs: dict[user_id -> prefs] including this user
    returns a harmony score in [0, 1]
    """
    # 1. Separate user vs others
    others = {uid: p for uid, p in group_prefs.items() if uid != user_id}
    if not others:
        return 1.0  # only user → trivially harmonious

    user_cuisine = (prefs.get("cuisine") or [])
    if isinstance(user_cuisine, str):
        user_cuisine = [user_cuisine]
    user_cuisine = [c.lower().strip() for c in user_cuisine]

    user_price = _normalize_price_raw(prefs.get("price_range") or prefs.get("price"))
    user_allergies = set((prefs.get("allergies") or []))

    # cuisine alignment (30%): compare with others' cuisines
    other_cuisines_raw = [
        (p.get("cuisine") or []) for p in others.values()
    ]
    other_cuisines_list: List[str] = []
    for item in other_cuisines_raw:
        if isinstance(item, str):
            other_cuisines_list.append(item.lower().strip())
        else:
            other_cuisines_list.extend([c.lower().strip() for c in item])

    cuisine_counts = Counter(other_cuisines_list)
    total_others = max(1, len(others))

    if not user_cuisine:
        cuisine_score = 0.5  # neutral if user didn't specify
    else:
        # take best overlap over user cuisine options
        same_cuisine_count = max(
            (cuisine_counts.get(c, 0) for c in user_cuisine),
            default=0,
        )
        cuisine_score = same_cuisine_count / total_others  # 0–1

    # price alignment (40%): compare with others' avg price
    other_prices = [
        _normalize_price_raw(p.get("price_range") or p.get("price"))
        for p in others.values()
    ]
    group_avg_price = float(np.mean(other_prices)) if other_prices else user_price

    price_diff = abs(user_price - group_avg_price)
    price_score = max(0.0, 1.0 - price_diff)  # linear penalty

        # allergy alignment (30%): penalize cuisines based on USER-SPECIFIC allergy risks
    # instead of a fixed risky cuisine list

    # Allergy → cuisine risk mapping (weights 0 to 1)
    ALLERGEN_RISK = {
        "peanut":   {"thai": 0.9, "vietnamese": 0.7, "chinese": 0.4},
        "soy":      {"chinese": 0.9, "japanese": 0.6, "korean": 0.4},
        "shellfish": {"sushi": 0.9, "chinese": 0.6, "thai": 0.4},
        "gluten":   {"italian": 0.8, "bakery": 0.9, "japanese": 0.5},
    }

    # Lowercase user allergies
    user_allergies = set(a.lower().strip() for a in user_allergies)

    # Compute weighted allergy risk from the cuisines the group prefers
    if not user_allergies:
        allergy_score = 1.0
    else:
        total_risk = 0.0
        count = 0
        for cuisine in other_cuisines_list:
            c = cuisine.lower().strip()
            for allergen in user_allergies:
                risk = ALLERGEN_RISK.get(allergen, {}).get(c, 0.1)  # 0.1 default small risk
                total_risk += risk
                count += 1
        avg_risk = (total_risk / count) if count > 0 else 0.0

        allergy_score = max(0.0, min(1.0, 1.0 - avg_risk))


    # Combine with weights 
    harmony = (
        0.3 * cuisine_score +
        0.4 * price_score +
        0.3 * allergy_score
    )

    return float(max(0.0, min(harmony, 1.0)))


def harmony_to_label(score: float) -> str:
    """
    Convert numeric harmony score into a natural-language descriptor.
    """
    if score >= 0.8:
        return "very aligned with the group"
    elif score >= 0.6:
        return "mostly aligned with the group"
    elif score >= 0.4:
        return "somewhat different from the group"
    else:
        return "quite different from the group"


def compute_harmony(user_id: str, prefs: dict) -> float:
    """
    Wrapper used by main.py:
    - updates global user_prefs
    - builds group_prefs
    - calls compute_harmony_score(...)
    """
    user_prefs[user_id] = prefs
    group_prefs = dict(user_prefs)
    score = compute_harmony_score(user_id, prefs, group_prefs)
    return float(score)


def prefs_to_vec(prefs: dict) -> np.ndarray:
    """
    Convert prefs into a numeric vector for conflict / compromise logic.

    Shared vector space with restaurant_to_vec:
      [ price_norm, allergy_count, cuisine_one_hot... ]
    """
    price_norm = _normalize_price_raw(prefs.get("price"))
    allergies = prefs.get("allergies") or []
    allergy_count = float(len(allergies))

    cuisines = prefs.get("cuisine") or []
    if isinstance(cuisines, str):
        cuisines = [cuisines]
    cuisines = [c.lower() for c in cuisines]

    cuisine_vec: List[float] = []
    for cat in CUISINE_CATEGORIES:
        cuisine_vec.append(
            1.0 if any(cat in c for c in cuisines) else 0.0
        )

    vec = np.array([price_norm, allergy_count] + cuisine_vec, dtype="float32")
    return vec

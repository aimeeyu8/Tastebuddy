import numpy as np

user_prefs = {}

def prefs_to_vec(p: dict) -> np.ndarray:
    """
    convert a structured preference dict into a numeric vector for similarity.
    expected keys:
      - "cuisine": string
      - "price" or "price_range": int 1–4 or None
      - "allergies": list
    """

    raw_cuisine = p.get("cuisine") or ""
    cuisine = str(raw_cuisine).lower().strip()

    cuisine_categories = ["sushi", "ramen", "thai", "italian", "mexican", "american"]
    cuisine_vec = [1.0 if cuisine == cat else 0.0 for cat in cuisine_categories]

    raw_price = p.get("price_range") or p.get("price")
    try:
        price_val = int(raw_price) if raw_price is not None else 0
    except (ValueError, TypeError):
        price_val = 0

    price_val = max(0, min(price_val, 4))
    price_norm = price_val / 4.0

    allergies = p.get("allergies") or []
    allergy_count = float(len(allergies))

    vec = [price_norm, allergy_count] + cuisine_vec
    return np.array(vec, dtype="float32")


def compute_harmony(user_id: str, prefs: dict) -> float:
    user_prefs[user_id] = prefs

    if len(user_prefs) <= 1:
        return 1.0

    other_vecs = [
        prefs_to_vec(p)
        for uid, p in user_prefs.items()
        if uid != user_id
    ]

    if not other_vecs:
        return 1.0

    group_avg = np.mean(other_vecs, axis=0)
    user_vec = prefs_to_vec(prefs)

    user_norm = np.linalg.norm(user_vec)
    group_norm = np.linalg.norm(group_avg)

    if user_norm == 0 or group_norm == 0:
        return 0.0

    similarity = float(np.dot(user_vec, group_avg) / (user_norm * group_norm))
    return similarity

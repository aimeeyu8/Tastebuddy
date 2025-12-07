import numpy as np

user_prefs = {}

def prefs_to_vec(p: dict) -> np.ndarray:
    raw_cuisine = (p.get("cuisine") or [""])[0].lower().strip()

    cuisine_categories = ["sushi", "ramen", "thai", "italian", "mexican", "american"]
    cuisine_vec = [1.0 if raw_cuisine == cat else 0.0 for cat in cuisine_categories]

    raw_price = p.get("price")
    try:
        price_val = int(raw_price) if raw_price else 0
    except:
        price_val = 0

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

    group_avg = np.mean(other_vecs, axis=0)
    user_vec = prefs_to_vec(prefs)

    user_norm = np.linalg.norm(user_vec)
    group_norm = np.linalg.norm(group_avg)

    if user_norm == 0 or group_norm == 0:
        return 0.0

    return float(np.dot(user_vec, group_avg) / (user_norm * group_norm))


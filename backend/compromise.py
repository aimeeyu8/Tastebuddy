import numpy as np

def restaurant_to_vec(r):
    """
    Turn restaurant attributes into a small vector for scoring.
    """
    rating = float(r.get("rating", 3.5))
    price = r.get("price", "")

    # Normalize price
    if price and price[0].isdigit():
        price_val = int(price[0]) / 4
    else:
        price_val = 0.5

    # Cuisine/type hashed to 0–1
    cuisine = r.get("type", "")
    cuisine_val = (abs(hash(cuisine)) % 200) / 200

    return np.array([rating / 5, price_val, cuisine_val], dtype="float32")


def best_compromise_restaurant(restaurants, group_avg_prefs):
    """
    Select the restaurant whose vector is closest to the group's preference vector.
    """
    if not restaurants:
        return None

    best = None
    best_sim = -1

    for r in restaurants:
        vec = restaurant_to_vec(r)

        dot = np.dot(vec, group_avg_prefs)
        denom = np.linalg.norm(vec) * np.linalg.norm(group_avg_prefs)
        sim = dot / denom if denom else 0

        if sim > best_sim:
            best_sim = sim
            best = r

    return best, float(best_sim)

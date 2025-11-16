import numpy as np

# Stores everyone’s preferences across the group
user_prefs = {}

def prefs_to_vec(p):
    vec = []

    # cuisine to stable mapping
    cuisine_map = {
        "sushi": 0, "ramen": 1, "thai": 2, "italian": 3, "mexican": 4,
        "spicy": 5, "cheap": 6, "american": 7
    }
    cuisine = p.get("cuisine", ["unknown"])[0].lower()
    cuisine_idx = cuisine_map.get(cuisine, 99)
    vec.append(cuisine_idx)

    # SAFE price digit parsing
    p_price = p.get("price", "")
    if not p_price or p_price == "":
        price_digit = 1
    else:
        try:
            price_digit = int(p_price[0])
        except:
            price_digit = 1

    vec.append(price_digit)

    # allergy count
    vec.append(len(p.get("allergies", [])))

    return np.array(vec, dtype="float32")

def compute_harmony(user_id, prefs):
    user_prefs[user_id] = prefs

    if len(user_prefs) <= 1:
        return 1.0

    # Build vectors EXCEPT current user
    others = [prefs_to_vec(p) for uid, p in user_prefs.items() if uid != user_id]

    if not others:
        return 1.0

    group_avg = np.mean(others, axis=0)
    user_vec = prefs_to_vec(prefs)

    similarity = float(
        np.dot(user_vec, group_avg) /
        (np.linalg.norm(user_vec) * np.linalg.norm(group_avg))
    )

    return similarity

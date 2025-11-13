import numpy as np
user_prefs = {}

def prefs_to_vec(p):
    vec = [hash(x) % 1000 for x in p.get("cuisine", [])]
    vec.append(len(p.get("allergies", [])))
    vec.append(int(p.get("price", "1")[0]))
    return np.array(vec, dtype="float32")

def compute_harmony(user_id, prefs):
    user_prefs[user_id] = prefs
    if len(user_prefs) <= 1:
        return 1.0
    vectors = [prefs_to_vec(p) for p in user_prefs.values()]
    avg = sum(vectors) / len(vectors)
    v = prefs_to_vec(prefs)
    return float(np.dot(v, avg) / (np.linalg.norm(v)*np.linalg.norm(avg)))

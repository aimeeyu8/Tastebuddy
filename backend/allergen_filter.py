import re

def filter_allergens(restaurants, allergies):
    """
    Filter out restaurants whose name or categories contain allergens.
    Returns a list of safe restaurants.
    """
    if not allergies:
        return restaurants

    safe = []
    for r in restaurants:
        text = (r.get("name", "") + " " + " ".join([c.get("title", "") for c in r.get("categories", [])])).lower()
        if not any(re.search(allergy.lower(), text) for allergy in allergies):
            safe.append(r)
    return safe
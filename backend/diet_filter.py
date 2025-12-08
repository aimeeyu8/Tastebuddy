# backend/diet_filter.py

import re
from typing import List


def filter_dietary_rules(restaurants: List[dict], diet_rules: List[str]) -> List[dict]:
    """
    Flexible filtering for many dietary needs.

    diet_rules is a list like:
        ["no pork", "gluten-free", "vegan", "no spicy"]

    Restaurants are filtered based on:
        - name (title)
        - type/category text
        - address text
    """
    if not diet_rules:
        return restaurants

    safe = []

    for r in restaurants:
        text = (
            (r.get("title") or "")
            + " "
            + (r.get("type") or "")
            + " "
            + " ".join((r.get("address") or "").split())
        ).lower()

        banned = False

        for rule in diet_rules:
            rule = rule.lower().strip()

            # Exclusion rules
            if rule in ["no pork", "pork-free", "avoid pork"]:
                if re.search(r"pork|tonkotsu", text):
                    banned = True

            if rule in ["no beef", "beef-free"]:
                if re.search(r"beef|steak|brisket", text):
                    banned = True

            if rule in ["no chicken", "chicken-free"]:
                if "chicken" in text:
                    banned = True

            if rule in ["no shellfish", "shellfish-free"]:
                if re.search(r"shrimp|lobster|crab|clam", text):
                    banned = True

            if rule in ["no nuts", "nut-free"]:
                if re.search(r"peanut|almond|cashew|walnut", text):
                    banned = True

            if rule in ["no dairy", "dairy-free"]:
                if re.search(r"cheese|cream|milk|butter", text):
                    banned = True

            if rule in ["no gluten", "gluten-free"]:
                if re.search(r"wheat|ramen|bread|pasta", text):
                    banned = True

            if rule in ["no soy", "soy-free"]:
                if "soy" in text:
                    banned = True

            if rule in ["no spicy", "not spicy"]:
                if "spicy" in text:
                    banned = True

            # Inclusion-type rules

            if rule in ["vegan"]:
                if not re.search(r"vegan|plant|vegetable", text):
                    banned = True

            if rule in ["vegetarian"]:
                if not re.search(r"veg", text):
                    banned = True

            if rule in ["halal"]:
                if "halal" not in text:
                    banned = True

            if rule in ["kosher"]:
                if "kosher" not in text:
                    banned = True

            if rule in ["healthy", "light", "low calorie", "low-calorie"]:
                if not re.search(r"healthy|salad|light|fresh", text):
                    banned = True

            if rule in ["low sugar", "sugar-free"]:
                if "dessert" in text or "cake" in text or "ice cream" in text:
                    banned = True

            if rule in ["low carb", "keto"]:
                if re.search(r"bread|rice|noodle|pasta", text):
                    banned = True

        if not banned:
            safe.append(r)

    return safe

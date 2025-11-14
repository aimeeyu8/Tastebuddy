# backend/dietary_filter.py
import re

def filter_dietary_rules(restaurants, diet_rules):
    """
    Flexible filtering for many dietary needs.

    diet_rules is a list like:
        ["no pork", "gluten-free", "vegan", "no spicy"]

    Restaurants are filtered based on:
        - name
        - type/category text
        - price description
        - description keywords (if available)

    Since SerpAPI Yelp data is limited (~ title/type), we match text patterns.
    """

    if not diet_rules:
        return restaurants

    safe = []

    for r in restaurants:
        text = (
            (r.get("title") or "") + " "
            + (r.get("type") or "") + " "
            + " ".join(r.get("address", "").split())
        ).lower()

        banned = False

        for rule in diet_rules:
            rule = rule.lower().strip()

            # exclusion rules
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

            #must include/requirements
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

        # If the restaurant passed every rule → keep it
        if not banned:
            safe.append(r)

    return safe

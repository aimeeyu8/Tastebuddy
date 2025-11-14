# backend/tests/eval_ranking.py
from main import rank_restaurants  # uses the function you defined in main.py

def run_ranking_tests():
    # Fake preferences: user wants ramen, cheap
    prefs = {
        "cuisine": ["ramen"],
        "price": "1",  # cheap
        "allergies": [],
        "location": "New York City",
        "mood": "",
        "dislikes": [],
    }
    diet_exclusions = []  # no special rules here

    restaurants = [
        {
            "title": "Fancy Ramen",
            "type": "Ramen",
            "address": "Rich St",
            "rating": 4.9,
            "price": "$$$$",
        },
        {
            "title": "Budget Ramen",
            "type": "Ramen",
            "address": "Cheap St",
            "rating": 4.4,
            "price": "$",
        },
        {
            "title": "Okay Ramen",
            "type": "Ramen",
            "address": "Middle Rd",
            "rating": 4.6,
            "price": "$$",
        },
    ]

    ranked = rank_restaurants(restaurants, prefs, diet_exclusions)

    print("\n=== Ranking Sanity Test ===\n")
    for r in ranked:
        print(f"{r['title']}  | rating={r['rating']}  | price={r['price']}")

    # Simple check: Budget Ramen should not be at the very bottom
    print("\nTop choice:", ranked[0]["title"])
    print("Bottom choice:", ranked[-1]["title"])


if __name__ == "__main__":
    run_ranking_tests()

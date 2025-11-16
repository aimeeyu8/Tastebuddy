# backend/tests/eval_harmony.py
from harmony_score import compute_harmony, prefs_to_vec, user_prefs

def reset():
    user_prefs.clear()

def run_harmony_tests():
    print("\n Harmony Score Evaluation \n")

    # Reset global stored preferences
    reset()

    # User 1: sushi
    u1 = {"cuisine": ["sushi"], "price": "2", "allergies": [], "location": "NYC"}
    h1 = compute_harmony("Cassidy", u1)
    print(f"Cassidy harmony: {h1:.2f} (expected: 1.00 baseline)")

    # User 2: sushi (similar)
    u2 = {"cuisine": ["sushi"], "price": "2", "allergies": [], "location": "NYC"}
    h2 = compute_harmony("Kelly", u2)
    print(f"Kelly harmony: {h2:.2f} (expected: high ~0.8–1.0)")

    # User 3: ramen (different cuisine)
    u3 = {"cuisine": ["ramen"], "price": "2", "allergies": [], "location": "NYC"}
    h3 = compute_harmony("Aimee", u3)
    print(f"Aimee harmony: {h3:.2f} (expected: medium ~0.3–0.6)")

    # User 4: vegan (very different)
    u4 = {"cuisine": ["vegan"], "price": "1", "allergies": [], "location": "NYC"}
    h4 = compute_harmony("Jamie", u4)
    print(f"Jamie harmony: {h4:.2f} (expected: low ~0.1–0.3)")

    print("\nInterpretation:")
    print("- Score should start at 1.0 for the first user.")
    print("- Users with similar cuisine should have high harmony.")
    print("- Users with different cuisines should show reduced harmony.")
    print("- Vegan vs sushi should be lowest of all.")


if __name__ == "__main__":
    run_harmony_tests()

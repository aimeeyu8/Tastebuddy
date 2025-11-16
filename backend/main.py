# backend/main.py
from dotenv import load_dotenv
import os
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from llm_engine import extract_preferences
from yelp_fetch import get_restaurants
from allergen_filter import filter_allergens
from harmony_score import compute_harmony, user_prefs, prefs_to_vec
from compromise import best_compromise_restaurant
from context_manager import update_context, get_context
from diet_filter import filter_dietary_rules


app = FastAPI(title="TasteBuddy Backend (Yelp + LLM + Harmony)")


# Allow frontend–backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatInput(BaseModel):
    user_id: str
    message: str


@app.get("/")
def root():
    return {"message": "TasteBuddy backend running with Yelp + LLM + Harmony."}

# Restaurant ranking system
def rank_restaurants(restaurants, prefs, diet_exclusions):
    """
    Scores each restaurant and sorts them based on:
        • Rating: 50%
        • Cuisine match: 20%
        • Price match: 20%
        • Dietary friendliness: 10%
    """

    ranked = []
    user_cuisine = (prefs.get("cuisine") or [""])[0].lower()
    user_price_pref = prefs.get("price") or "1,2,3,4"

    for r in restaurants:
        score = 0.0

        # Rating weight
        rating = float(r.get("rating") or 0)
        score += (rating / 5.0) * 0.50

        # Cuisine match weight
        rest_type = (r.get("type") or "").lower()
        if user_cuisine and user_cuisine in rest_type:
            score += 0.20

        # Price match weight
        rest_price = r.get("price") or ""
        if rest_price and rest_price[0] in user_price_pref:
            score += 0.20

        # Dietary friendliness weight
        rest_text = (
            f"{r.get('title','')} {r.get('type','')} {r.get('address','')}"
        ).lower()

        diet_friendly = True
        for rule in diet_exclusions:
            keyword = rule.replace("no ", "").strip()
            if keyword in rest_text:
                diet_friendly = False

        if diet_friendly:
            score += 0.10

        ranked.append((r, score))

    ranked.sort(key=lambda x: x[1], reverse=True)
    return [item[0] for item in ranked]


# Main chat endpoint
@app.post("/chat")
def chat(input: ChatInput):

    try:
        # Save conversation memory
        update_context(input.user_id, input.message)

        # Structured preferences from LLM
        prefs = extract_preferences(input.message)
        msg_lower = input.message.lower()

        # ---------------------------------------------
        # Detect dietary restrictions and allergies
        # ---------------------------------------------
        diet_exclusions = []
        extra_allergies = []

        if "no pork" in msg_lower:
            diet_exclusions.append("no pork")
        if "no beef" in msg_lower:
            diet_exclusions.append("no beef")
        if "no chicken" in msg_lower:
            diet_exclusions.append("no chicken")
        if "vegetarian" in msg_lower or "no meat" in msg_lower:
            diet_exclusions.append("vegetarian")
        if "vegan" in msg_lower:
            diet_exclusions.append("vegan")

        # Dairy-free
        if any(x in msg_lower for x in ["no dairy", "dairy-free", "milk-free", "no milk"]):
            extra_allergies.extend(["dairy", "milk"])
            diet_exclusions.append("no dairy")

        # Gluten-free
        if "gluten-free" in msg_lower or "no gluten" in msg_lower:
            diet_exclusions.append("gluten-free")

        # No spicy
        if "no spicy" in msg_lower or "not spicy" in msg_lower:
            diet_exclusions.append("no spicy")

        # Resolve cuisine fallback
        cuisine_list = prefs.get("cuisine") or []

        if len(cuisine_list) == 0:
            if any(s in msg_lower for s in ["sweet", "dessert", "cake", "cookie", "ice cream"]):
                cuisine = "dessert"
            else:
                cuisine = "food"
        else:
            cuisine = cuisine_list[0]

        # Fallbacks
        price = prefs.get("price") or "1,2,3,4"
        location = prefs.get("location") or "New York City"
        allergies = (prefs.get("allergies") or []) + extra_allergies

        harmony = compute_harmony(input.user_id, prefs)

        # Query Yelp
        yelp_data = get_restaurants(term=cuisine, location=location, limit=5)
        restaurants = yelp_data.get("businesses", [])

        # Apply filtering
        safe_restaurants = filter_allergens(restaurants, allergies)
        safe_restaurants = filter_dietary_rules(safe_restaurants, diet_exclusions)

        # If nothing remains after filtering
        if not safe_restaurants:
            reply = (
                f"I looked for {cuisine} in {location}, but found no safe options "
                f"for allergies {allergies} or dietary rules {diet_exclusions}."
            )
            return {
                "reply": f"(Harmony Score: {harmony:.2f})\n\n" + reply,
                "preferences": prefs,
                "restaurants": [],
                "harmony_score": harmony,
                "context": get_context(input.user_id),
            }

        # Apply ranking system
        ranked = rank_restaurants(safe_restaurants, prefs, diet_exclusions)

        # Group compromise
        conflict_section = ""
        best_rest = None
        best_sim = None

        if len(user_prefs) > 1:
            conflict_section += "🟦 Group conflict analysis:\n"

            for uid, up in user_prefs.items():
                c_list = up.get("cuisine") or ["unknown"]
                pref_c = c_list[0]
                conflict_section += f"- {uid} prefers: {pref_c}\n"

            vecs = [prefs_to_vec(p) for p in user_prefs.values()]
            group_avg = np.mean(vecs, axis=0)

            best_rest, best_sim = best_compromise_restaurant(ranked, group_avg)

            conflict_section += "\n🟪 Best compromise restaurant:\n"
            if best_rest:
                conflict_section += (
                    f"{best_rest.get('title')} – {best_rest.get('type')} – "
                    f"{best_rest.get('price','?')}, {best_rest.get('rating','?')}★\n"
                    f"Reason: best fit for the whole group (similarity {best_sim:.2f}).\n\n"
                )

        # Build list of ranked restaurants
        lines = []
        for r in ranked[:5]:
            lines.append(
                f"- {r.get('title')} ({r.get('type','')}) – "
                f"{r.get('price','?')}, {r.get('rating','?')}★ – {r.get('address','')}"
            )

        reply = conflict_section + "Here are safe options:\n\n" + "\n".join(lines)

        # Add safety warning
        if any(a.lower() in ["peanut", "peanuts", "milk", "dairy", "soy", "shellfish"] for a in allergies):
            reply = (
                "⚠️ Allergy Safety Warning: Ingredient-level safety is unknown. Call the restaurant.\n\n"
                + reply
            )

        return {
            "reply": f"(Harmony Score: {harmony:.2f})\n\n" + reply,
            "preferences": prefs,
            "restaurants": ranked[:5],
            "harmony_score": harmony,
            "context": get_context(input.user_id),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Reset memory endpoint
@app.post("/reset_memory")
def reset_memory():
    global user_prefs

    try:
        import json
        FILE = "data/conversation_memory.json"
        json.dump({}, open(FILE, "w"), indent=2)
    except:
        pass

    user_prefs.clear()

    return {"status": "ok", "message": "All memory cleared."}

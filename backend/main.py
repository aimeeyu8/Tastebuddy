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

app = FastAPI(title="TasteBuddy Backend (Yelp + LLM)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ok for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatInput(BaseModel):
    user_id: str
    message: str

@app.get("/")
def root():
    return {"message": "TasteBuddy backend running with Yelp."}

@app.post("/chat")
def chat(input: ChatInput):
    """
    Flow:
    1. Use LLM to extract preferences from message.
    2. Query Yelp with cuisine/location/price.
    3. Filter restaurants by allergies.
    4. Build a reply string summarizing recommendations.
    """
    try:
        prefs = extract_preferences(input.message)

        cuisine_list = prefs.get("cuisine") or ["food"]
        cuisine = cuisine_list[0]
        price = prefs.get("price") or "1,2,3,4"
        location = prefs.get("location") or "New York City"
        allergies = prefs.get("allergies") or []

        # Call Yelp
        yelp_data = get_restaurants(term=cuisine, location=location, price=price, limit=5)
        restaurants = yelp_data.get("businesses", [])

        # Filter by allergies
        safe_restaurants = filter_allergens(restaurants, allergies)

        # Build reply text
        if not safe_restaurants:
            reply = (
                f"I tried looking for {cuisine} in {location}, "
                f"but couldn't find good matches given the allergies {allergies}. "
                "Maybe try changing cuisine, area, or allergy constraints?"
            )
        else:
            
            lines = []
            for r in safe_restaurants[:5]:
                name = r.get("title")
                rating = r.get("rating", "?")
                price_sym = r.get("price", "?")
                category = r.get("type", "")
                address = r.get("address", "")

                lines.append(f"- {name} ({category}) – {price_sym}, {rating}★ – {address}")

            reply = (
                f"Based on what you said, I'm looking for {cuisine} around {location}.\n"
                f"Here are some Yelp suggestions that avoid your allergies {allergies}:\n\n"
                + "\n".join(lines)
            )

        return {
            "reply": reply,
            # Optional: include raw data if you ever want to use it in the frontend
            "preferences": prefs,
            "restaurants": safe_restaurants[:5],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

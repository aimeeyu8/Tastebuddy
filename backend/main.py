# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llm_engine import extract_preferences
from yelp_fetch import get_restaurants
#from context_manager import update_context, get_context
#from allergen_filter import filter_allergens
#from harmony_score import compute_harmony
import json

app = FastAPI(title="TasteBuddy LLM API")

# Allow local frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request body schema
class ChatInput(BaseModel):
    user_id: str
    message: str


@app.get("/")
def root():
    return {"message": "TasteBuddy backend running."}


@app.post("/chat")
def chat(input: ChatInput):
    """
    1. Add message to user's context
    2. Extract preferences using OpenAI
    3. Get restaurant data from Yelp
    4. Filter allergens and compute harmony score
    5. Return structured recommendations
    """
    try:
        update_context(input.user_id, input.message)

        prefs_json = extract_preferences(input.message)
        prefs = json.loads(prefs_json)

        cuisine = prefs.get("cuisine", ["food"])[0]
        price = prefs.get("price", "1,2,3,4")
        location = prefs.get("location", "New York City")
        allergies = prefs.get("allergies", [])

        yelp_data = get_restaurants(term=cuisine, location=location, price=price)
        restaurants = yelp_data.get("businesses", [])

        # Filter unsafe restaurants
        safe_restaurants = filter_allergens(restaurants, allergies)

        # Compute harmony score placeholder
        harmony_score = compute_harmony(input.user_id, prefs)

        response = {
            "user": input.user_id,
            "preferences": prefs,
            "harmony_score": harmony_score,
            "recommendations": safe_restaurants[:5],
            "context": get_context(input.user_id),
        }
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

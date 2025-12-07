# backend/llm_engine.py
import os
import json
from pathlib import Path
from typing import Optional, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

# load .env from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are TasteBuddy, a friendly restaurant assistant for group chats in New York City.

STYLE:
- Sound like a helpful friend, not a corporate chatbot.
- Use simple, natural language and contractions (like "don’t", "you’ll").
- Keep answers short: 1–3 short paragraphs or a few bullet points.
- Avoid over-explaining how you work or mentioning being an AI.

TASK:
- Read what people say about what they want to eat.
- Infer cuisine, budget, allergies, likes/dislikes, location hints, and mood.
- Suggest 3–5 restaurant ideas in NYC tailored to them.
- Mention why each place might be a good fit (vibe, price, group size, etc.).
- Be honest when you’re unsure and avoid making up non-existing restaurants.
"""


PREF_SYSTEM_PROMPT = """
Extract structured restaurant preferences from text.
Return JSON with keys:
- cuisine: list of strings
- price: string like "1,2,3,4" or "2" etc.
- allergies: list of strings
- location: string (default "New York City" if not given)
- mood: string
- dislikes: list of strings
"""

def chat_with_tastebuddy(message: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        temperature=0.5,
    )
    return resp.choices[0].message.content

# preference extraction
def extract_preferences(text: str) -> dict:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": PREF_SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    prefs = json.loads(resp.choices[0].message.content)

    text_lower = text.lower()
    price = None

    cheap_words = ["cheap", "affordable", "inexpensive", "budget"]
    moderate_words = ["not too expensive", "moderate", "mid-range", "okay price"]
    expensive_words = ["expensive", "fancy", "pricey", "high-end"]

    if any(w in text_lower for w in cheap_words):
        price = "1"
    elif any(w in text_lower for w in moderate_words):
        price = "2"
    elif any(w in text_lower for w in expensive_words):
        price = "3,4"
    elif "$$$$" in text_lower:
        price = "4"
    elif "$$$" in text_lower:
        price = "3"
    elif "$$" in text_lower:
        price = "2"
    elif "$" in text_lower:
        price = "1"
    if price:
        prefs["price"] = price
    elif prefs.get("price") not in ["1", "2", "3", "4", "1,2", "3,4"]:
        prefs["price"] = "1,2,3,4"

    return prefs

def generate_final_reply(
    user_query: str,
    prefs: dict,
    restaurants: List[dict],
    notes: Optional[Dict] = None,
) -> str:
    """
    Generate a friendly, human-style reply that:
    - references the user's original query,
    - uses the parsed preferences,
    - and talks about the final restaurant list.
    """

    # 1) Handle "no restaurants" edge case
    if not restaurants:
        return (
            "I couldn’t find any places that match those filters 😢\n"
            "If you’re okay relaxing the budget, location, or allergy rules a bit, "
            "I can try again with a wider search."
        )

    notes = notes or {}
    restaurants_summary: List[Dict] = []

    # 2) Limit to top 5 to keep prompt small
    top_restaurants = restaurants[:5]

    for r in top_restaurants:
        loc = r.get("location")
        if isinstance(loc, dict):
            neighborhood = (
                loc.get("neighborhood")
                or ", ".join(loc.get("display_address", []))
                or None
            )
        else:
            neighborhood = None

        restaurants_summary.append({
            "name": r.get("title") or r.get("name"),
            "rating": r.get("rating"),
            "price": r.get("price", "?"),
            "neighborhood": neighborhood,
            "categories": [c.get("title", "") for c in r.get("categories", [])],
        })

    prompt = f"""
User query:
{user_query}

Parsed preferences (from previous step):
{json.dumps(prefs, indent=2)}

Final restaurant candidates (after Yelp + filters):
{json.dumps(restaurants_summary, indent=2)}

Extra notes (optional):
{json.dumps(notes, indent=2)}

Write a short, friendly reply to the user as "TasteBuddy":
- Start with 1–2 sentences acknowledging what they’re looking for (cuisine, budget, vibe, group).
- Then recommend these places from the list above.
- For each place, mention:
  - what kind of spot it is (vibe),
  - how it fits their request (price, mood, group size, etc.),
  - anything about neighborhood if available.
- If allergens or diet filters removed some places, briefly reassure them that you filtered out risky options.
- Keep the tone casual and natural, like a friend texting suggestions.
- Do NOT invent restaurants that are not in the list above.
""".strip()

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    return resp.choices[0].message.content



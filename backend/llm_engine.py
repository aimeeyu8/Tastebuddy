# backend/llm_engine.py
# this file extracts user preferences from chat messages and generates the reply
# uses openAi API and gpt-4o-mini model
import os
import json
from pathlib import Path
from typing import Optional, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

# Load .env to get api keys
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# init openai client
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
- diet: list of strings like ["vegan", "no pork", "gluten-free"]
"""

# below is currently unused, we can probably take this out
def chat_with_tastebuddy(message: str) -> str:
    """(Currently unused) Simple direct-chat helper."""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        temperature=0.5,
    )
    return resp.choices[0].message.content


def extract_preferences(text: str) -> dict:
    # sends message to llm with json format, then converts the response to python dict
    """
    Returns dict like:
    {
        "cuisine": ["ramen"],
        "price": "1,2",
        "allergies": ["dairy"],
        "location": "New York City",
        "mood": "spicy",
        "dislikes": [],
        "diet": ["no pork", "vegan"]
    }
    """
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

    # --------- hybrid price correction layer ----------
    text_lower = text.lower()
    price = None

    # words associated with cheap, moderate, expensive
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
        # if LLM gave something weird, default to full range
        prefs["price"] = "1,2,3,4"

    # Normalize diet field: always a list of strings
    diet = prefs.get("diet") or []
    if isinstance(diet, str):
        diet = [diet]
    prefs["diet"] = [d.strip() for d in diet if d.strip()]

    return prefs

# final outputted recommendation text
def generate_final_reply(
    user_query: str,
    prefs: dict,
    restaurants: List[dict],
    notes: Optional[Dict] = None,
) -> str:
    """
    Generate a friendly, short, human-style reply that:
    - references the user's original query,
    - uses the parsed preferences,
    - and talks about the final restaurant list.
    """

    if not restaurants:
        return (
            "I couldn’t find any places that match those filters\n"
            "If you’re okay relaxing the budget, location, or allergy rules a bit, "
            "I can try again with a wider search."
        )

    notes = notes or {}
    restaurants_summary: List[Dict] = []

    # Limit to top 5 for smaller prompt
    top_restaurants = restaurants[:5]

    for r in top_restaurants:
        # We normalized data, so we know these fields exist
        neighborhood = r.get("neighborhood")

        restaurants_summary.append({
            "name": r.get("title") or r.get("name"),
            "rating": r.get("rating"),
            "price": r.get("price", "?"),
            "neighborhood": neighborhood,
            "categories": [
                c["title"] if isinstance(c, dict) and "title" in c else str(c)
                for c in r.get("categories", [])
            ],

        })
    # Look at the allergy info inputted by the user for safety disclaimer of the model 
    allergies = notes.get("allergies") or prefs.get("allergies") or []

    # Build a small extra instruction about allergens
    if allergies:
        allergy_instruction = (
            "The user mentioned these allergies: "
            f"{', '.join(allergies)}. You can say that the system tried to "
            "avoid places where those allergens appear clearly in menu or review text, "
            "but you MUST remind them to double-check menus and ask the staff. "
            "Do NOT say that any restaurant is completely safe or guaranteed allergen-free."
        )
    else:
        allergy_instruction = (
            "If you mention safety, keep it general. "
            "Do NOT claim that all allergens were removed or that places are guaranteed safe."
        )

    prompt = f"""
User query:
{user_query}

Parsed preferences (from previous step):
{json.dumps(prefs, indent=2)}

Final restaurant candidates (after Yelp + filters + ranking):
{json.dumps(restaurants_summary, indent=2)}

Extra notes (optional):
{json.dumps(notes, indent=2)}

Write a short, friendly reply to the user as "TasteBuddy":
- Start with 1–2 sentences acknowledging what they’re looking for (cuisine, allergy, budget, vibe, group).
- Then recommend up to 3 places from the list above.
- Do NOT repeat the restaurant list twice.
- For each place, mention:
  - what kind of spot it is (vibe),
  - how it fits their request (price, mood, group size, etc.),
  - anything about neighborhood if available.
- If allergens or diet filters removed some places, briefly reassure them that you filtered out risky options.
- {allergy_instruction}
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

    reply_text = resp.choices[0].message.content

    #remove the top recommendations to reduce redundancy 
    trigger = "Top Recommendations"
    if trigger in reply_text:
        reply_text = reply_text.split(trigger)[0].strip()

    #make sure our model has safety disclaimer 
    unsafe_phrases = [
        "I didn’t include any risky options",
        "I didn't include any risky options",
        "so you can feel good about these choices",
        "so you can feel safe about these choices",
        "so you can feel safe choosing any of these",
    ]
    for phrase in unsafe_phrases:
        if phrase in reply_text:
            reply_text = reply_text.replace(
                phrase,
                "These seem like good matches, but please still double-check the menu and ask the staff about any allergies."
            )

    return reply_text

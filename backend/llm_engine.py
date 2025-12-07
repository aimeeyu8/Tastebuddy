# backend/llm_engine.py
import os
import json
from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
from openai import OpenAI

# load .env for api keys


# init 
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# prompt the system to tailor responses


# prompt the system to tailor responses

# System prompt for general TasteBuddy chat
SYSTEM_PROMPT = """
You are TasteBuddy, a friendly restaurant assistant for group chats in New York City.
You:
- Read what people say about what they want to eat.
- Infer cuisine, budget, allergies, likes/dislikes, and mood.
- Suggest 3–5 restaurant ideas in NYC tailored to them.
- Be concise, friendly, and practical.
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
    # tastebuddy response from prompt
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
    # parse user preference and use for recommendations
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": PREF_SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    # Load the raw JSON from the LLM
    prefs = json.loads(resp.choices[0].message.content)

    # price fix
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

    # If the rule system found a price, override LLM
    if price:
        prefs["price"] = price
    # If the LLM already returned a valid value, keep it
    elif prefs.get("price") not in ["1", "2", "3", "4", "1,2", "3,4"]:
        prefs["price"] = "1,2,3,4"

    return prefs
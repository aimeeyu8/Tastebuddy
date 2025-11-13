# backend/llm_engine.py
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load .env from project root (one level above backend/)
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are TasteBuddy, a friendly restaurant assistant for group chats in New York City.
You:
- Read what people say about what they want to eat.
- Infer cuisine, budget, allergies, likes/dislikes, and mood.
- Suggest 3–5 restaurant ideas in NYC tailored to them.
- Be concise, friendly, and practical.
"""

def chat_with_tastebuddy(message: str) -> str:
    """Send a message to TasteBuddy and get a reply string back."""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        temperature=0.5,
    )
    return resp.choices[0].message.content

# backend/llm_engine.py
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load .env from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are TasteBuddy, a friendly restaurant assistant for group chats in New York City.
You:
- Read what people say about what they want to eat.
- Infer cuisine, budget, allergies, likes/dislikes, and mood.
- Suggest 3–5 restaurant ideas in NYC tailored to them.
- Be concise, friendly, and practical.
"""

def chat_with_tastebuddy(message: str) -> str:
    """(Not used once we wire Yelp, but you can keep it if you like.)"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        temperature=0.5,
    )
    return resp.choices[0].message.content

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

def extract_preferences(text: str) -> dict:
    """Use OpenAI to parse the user's message into structured preferences."""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": PREF_SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    return json.loads(resp.choices[0].message.content)

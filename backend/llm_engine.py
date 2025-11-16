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
    return json.loads(resp.choices[0].message.content)

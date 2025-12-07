# backend/llm_engine.py

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY is not set. Check your .env file.")

client = OpenAI(api_key=api_key)


def extract_preferences(message: str) -> str:
    """
    Ask the OpenAI model to extract user preferences.

    Returns:
        A JSON string with fields like:
        {
          "cuisine": ...,
          "price_range": ...,
          "location": ...,
          "allergies": [...]
        }
    """
    system_prompt = {
        "role": "system",
        "content": (
            "You are a restaurant assistant that extracts structured "
            "preferences from free text."
        ),
    }
    user_prompt = {
        "role": "user",
        "content": (
            "Extract cuisine, price_range (1–4), location, and allergies "
            f"from this text: {message}. "
            "Respond strictly in JSON with keys "
            '["cuisine", "price_range", "location", "allergies"].'
        ),
    }

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[system_prompt, user_prompt],
        temperature=0.3,  # a bit less randomness
    )

    raw = completion.choices[0].message.content

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {
            "cuisine": None,
            "price_range": None,
            "location": None,
            "allergies": [],
            "raw_response": raw,
        }
    return json.dumps(parsed)

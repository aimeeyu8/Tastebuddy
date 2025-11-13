from openai import OpenAI
import os
from dotenv import load_dotenv
from pathlib import Path

# Automatically locate and load the .env file
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
Extract structured restaurant preferences from text.
Return JSON with: cuisine (list), price, allergies (list), location, mood, dislikes (list).
"""

def extract_preferences(text: str) -> str:
    """Send user text to the OpenAI API and extract structured preferences."""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content
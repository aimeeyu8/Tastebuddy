# backend/llm_engine.py
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_preferences(message: str):
    """Ask OpenAI model to extract user preferences."""
    system_prompt = {
        "role": "system",
        "content": "You are a restaurant assistant that extracts structured preferences from free text."
    }
    user_prompt = {
        "role": "user",
        "content": f"Extract cuisine, price range (1–4), location, and allergies from this text: {message}. "
                   "Respond strictly in JSON format."
    }

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[system_prompt, user_prompt],
        temperature=0.5
    )
    return completion.choices[0].message.content

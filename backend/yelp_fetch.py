# backend/yelp_fetch.py
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root (one level above backend/)
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")

def get_restaurants(term, location="New York City", price="1,2,3,4", limit=5):
    """
    Uses SERPAPI Yelp engine instead of Yelp Fusion.
    No Bearer token, no 128-character requirement.
    """
    if not SERPAPI_KEY:
        raise RuntimeError("SERPAPI_API_KEY is not set in .env")

    params = {
        "engine": "yelp",
        "q": term,
        "find_loc": location,
        "api_key": SERPAPI_KEY,
    }

    response = requests.get("https://serpapi.com/search", params=params)
    response.raise_for_status()  # will raise HTTPError if SerpAPI returns 4xx/5xx

    data = response.json()
    businesses = data.get("local_results", [])

    # Normalize to look a bit like Yelp Fusion for the rest of your code
    normalized = []
    for b in businesses[:limit]:
        normalized.append({
            "title": b.get("title"),
            "rating": b.get("rating"),
            "price": b.get("price"),
            "type": b.get("type"),               # category
            "address": b.get("address"),         # single string
        })

    return {"businesses": normalized}

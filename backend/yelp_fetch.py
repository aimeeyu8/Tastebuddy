import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root (one level above backend/)
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")

def get_restaurants(term, location="New York City", price="1,2,3,4", limit=5):
    # use serpapi to get yelp information
    if not SERPAPI_KEY:
        raise RuntimeError("SERPAPI_API_KEY is not set in .env")

    params = {
        "engine": "google_local",
        "q": f"{term} restaurant",
        "location": location,
        "api_key": SERPAPI_KEY,
    }

    response = requests.get("https://serpapi.com/search", params=params)
    response.raise_for_status()

    data = response.json()
    local_results = data.get("local_results", [])

    normalized = []
    for b in local_results[:limit]:
        normalized.append({
            "title": b.get("title"),
            "rating": b.get("rating"),
            "price": b.get("price"),
            "type": b.get("type", ""),
            "address": b.get("address"),
        })

    return {"businesses": normalized}

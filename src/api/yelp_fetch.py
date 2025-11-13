# backend/yelp_fetch.py
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")

def get_restaurants(term, location="New York City", price="1,2,3,4", limit=5):
    """
    Uses SerpAPI Yelp Engine instead of Yelp Fusion API.
    MUCH easier—no need for Yelp's 128-char API key.
    """
    params = {
        "engine": "yelp",
        "q": term,
        "find_loc": location,
        "api_key": SERPAPI_KEY,
    }

    response = requests.get("https://serpapi.com/search", params=params)
    data = response.json()

    businesses = data.get("local_results", [])

    # Trim to limit
    return {"businesses": businesses[:limit]}

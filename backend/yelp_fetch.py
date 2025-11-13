# backend/yelp_fetch.py
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path="backend/.env")

API_KEY = os.getenv("SERPAPI_API_KEY")

if not API_KEY:
    raise ValueError("❌ Yelp API key not found. Check your .env file.")

def get_restaurants(term, location, price="1,2,3", limit=10):
    """
    Retrieve Yelp business listings based on search criteria.
    """
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    params = {
        "term": term,
        "location": location,
        "price": price,
        "limit": limit,
        "sort_by": "rating"
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise RuntimeError(f"Yelp API error {response.status_code}: {response.text}")

    return response.json()

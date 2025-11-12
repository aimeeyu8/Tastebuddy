from dotenv import load_dotenv
import os
import requests
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
serpapi_key = os.getenv("SERPAPI_API_KEY")
'''
params = {
    "engine": "yelp",     
    "q": "restaurants",
    "api_key": serpapi_key,
    "find_loc": "New York, NY, USA"
}
'''
# search = requests.get("https://serpapi.com/search", params=params)
# response = search.json()
# print(response)

def get_restaurants(term, location="New York City", price="1,2,3,4", limit=5):
    headers = {"Authorization": f"Bearer {serpapi_key}"}
    params = {"term": term, "location": location, "price": price, "limit": limit}
    r = requests.get("https://api.yelp.com/v3/businesses/search", headers=headers, params=params)
    return r.json()

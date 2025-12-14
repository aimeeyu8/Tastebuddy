# TasteBuddy: LLM Restaurant Assistant

TasteBuddy is a Large Language Model (LLM)-powered restaurant assistant that aims to solve the issue of picking restaurants in group settings. Unlike other solutions that use filtering, TasteBuddy hopes to understand multiple users’ chats and extracts each person's preferences, analyzes group alignment, filters out unsafe options, and recommends resturants using Yelp data and an LLM reasoning layer. TasteBuddy is built specifically for New York City dining, with safety!
---

## Features

- **Multi-User Chat**: Each user will be able to join the chat with their name. Messages are stores server-side and replayed across all conencted users. The model will read everyone's messages and generate response when tagged using @TasteBuddy.   

- **Allergen and Dietary Safety**: TasteBuddy includes a custom safety layer that analyzes each user’s allergies and dietary restrictions, then removes risky restaurants before the LLM generates recommendations.


- **Interactive Feedback Loop**  


---

## Methodology

1. **Data Collection** 
For every user request, TasteBuddy pulls live restaurant data directly from the Yelp Fusion API. Instead of storing a fixed dataset, the backend sends a real-time query based on the user's preferences on cuisine, location, and price. The API returns information  
2. **User Input Collection** 
3. **Preference Extraction** 
4. **LLM Reasoning and Ranking** 
5. **Allergen Filtering**
In our allergen filterings, we have two safety layers to support this function. 
    1. Rule-Based Filtering (the first safety layer): TasteBuddy looks at each restaurant’s Yelp categories and checks them against the user’s allergies or diet rules.
    Instead of guessing based on cuisine (like “Thai = peanuts”), it focuses on real keywords in the restaurant’s categories, such as “seafood,” “shellfish,” “peanut,” “cream,” “barbecue,” etc.
    If a restaurant clearly mentions something the user can’t have, we remove it immediately. This same rule system also handles diets like no-pork, halal, vegetarian, and vegan.

    2. LLM Safety Check (the second safety layer):
    After rule filtering, the remaining restaurants go through a lightweight LLM check. The model only sees the restaurant categories + the user’s allergens/diet, and decides if its recommendation is risky. The LLM acts as a final “human-like reasoning” step that catches edge cases the rule-based filter might miss.

Together, these two layers make sure the final recommendations feel inclusive, safe, and personalized, without being overly strict or accidentally blocking good restaurants.

6. **Conflict Resolution**  
7. **Feedback Loop**

---

## Tech Stack

- **Language Model:** OpenAI GPT  
- **Backend:** Python  
- **APIs:** Yelp API 
- **Visualization and Reports:** Python  
- **Data Analysis:** Pandas, Matplotlib  
- **Frontend:** HTML+CSS


## Contributors

Cassidy Francis, Kelly Lee, Aimee Yu

## Step-by-Step Tutorial: Running TasteBuddy

Below are full instructions for environment setup, API keys, backend frontend launch, and troubleshooting.
### 1. Required API Keys

TasteBuddy requires two API keys:

#### 1. OpenAI API Key

Create one at: https://platform.openai.com

Add it to your .env file inside backend/:

OPENAI_API_KEY=your_key_here

#### 2. Yelp Fusion API Key

Create one at: https://www.yelp.com/developers/v3/manage_app

Add it to backend/.env:

YELP_API_KEY=your_key_here

### 2. Installation Instructions
Windows Setup
cd Tastebuddy
cd backend

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

macOS / Linux Setup
cd Tastebuddy/backend

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

### 3. Running TasteBuddy (Backend + Frontend)

You now have two ways to run the system:

#### Option A — One-Click Launcher (Recommended)
Windows Users

Double-click:

run_tastebuddy.bat

(Or run inside VS Code terminal:)

cmd /c run_tastebuddy.bat


This will:

-Start backend on http://127.0.0.1:8000

-Start frontend on http://localhost:5500

Open your browser automatically

macOS / Linux Users

Use the shell version:

Install once:
chmod +x run_tastebuddy.sh

Run TasteBuddy:
./run_tastebuddy.sh


This does the same: Starts backend, Starts frontend & Opens the browser

#### Option B — Run Manually

If you prefer to run backend + frontend yourself:

Start the Backend
Windows
cd Tastebuddy/backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000

macOS/Linux
cd Tastebuddy/backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

Start the Frontend

Open a new terminal:

Windows / Mac / Linux:
cd Tastebuddy/frontend
python -m http.server 5500


Visit:http://localhost:5500

Usage Examples
Start a conversation:

Type:

Hi TasteBuddy!


Model responds when tagged:

@tastebuddy Find sushi in Midtown for someone gluten-free


### Troubleshooting Guide
1. "uvicorn not recognized"

Your virtual environment is not active.

Activate it again:

Windows

venv\Scripts\activate


macOS/Linux

source venv/bin/activate

2. "ImportError: attempted relative import"

You ran this command:

uvicorn main:app


Instead, always run from repo root:

uvicorn backend.main:app --reload --port 8000

3. Browser won’t load frontend

Make sure you started:

python -m http.server 5500


Then visit:http://localhost:5500

4. Allergen filter takes too long

This happens when SERPAPI’s Yelp Places API is slow or rate-limited.
Future improvements include:

Caching results

Switching to async requests

Reducing menu analysis depth

TasteBuddy Is Ready!

Your environment is set up, API keys are installed, and you can now launch the full system with one click on Windows or macOS/Linux.


## References

- Brahimi, S. (2024). *AI-Powered Dining: Text Information Extraction and Machine Learning for Personalized Menu Recommendations and Food Allergy Management.* International Journal of Information Technology, 17(4), 2107–2115.  
- Mao, M. et al. (2024). *Multi-User Chat Assistant (MUCA): A Framework Using LLMs to Facilitate Group Conversations.* arXiv preprint arXiv:2401.04883.

---

## About

TasteBuddy hopes to bring inclusive and personalized recommendations to users in group settings. 

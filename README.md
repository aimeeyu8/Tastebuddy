# TasteBuddy: LLM Restaurant Assistant

TasteBuddy is a Large Language Model (LLM)-powered restaurant assistant that aims to solve the issue of picking restaurants in group settings. Unlike other solutions that use filtering, TasteBuddy hopes to understand multiple users’ chats and extracts each person's preferences, analyzes group alignment, filters out unsafe options, and recommends resturants using Yelp data and an LLM reasoning layer. TasteBuddy is built specifically for New York City dining, with safety!
---

## Features

- **Multi-User Chat**: Each user will be able to join the chat with their name. Messages are stores server-side and replayed across all conencted users. The model will read everyone's messages and generate response when tagged using @TasteBuddy.   

- **Allergen and Dietary Safety**: TasteBuddy includes a custom safety layer that analyzes each user’s allergies and dietary restrictions, then removes risky restaurants before the LLM generates recommendations.

---

## Methodology

1. **Data Collection** 
For every user request, TasteBuddy pulls live restaurant data directly from the Yelp Fusion API. Instead of storing a fixed dataset, the backend sends a real-time query based on the user's preferences on cuisine, location, and price. The API returns information  
2. **User Input Collection**
Users interact with TasteBuddy through a shared chat interface. Messages are stored with user identity so the system can track preferences across multiple users.
3. **Preference Extraction**
An LLM extracts structured preferences such as cuisine, price, allergies, diet, and location from natural-language input. Rule-based normalization is then applied to ensure consistency across users.
4. **Harmony Score**
The harmony score summarizes how compatible users are by combining price, cuisine, and allergy preferences, and it triggers conflict handling when users disagree too much.
5. **Allergen and Diet Filtering**
Restaurant menus and review text are analyzed to estimate allergen risk. Restaurants with a high percentage of allergen-containing items are filtered out for safety.
6. **LLM Reasoning and Ranking**
After filtering, restaurants are scored using a weighted ranking system based on safety, price match, cuisine relevance, ratings, and reviews. The LLM explains the ranked results in a natural and conversational way.
7. **Conflict Resolution**
When multiple users have conflicting preferences, the system computes a harmony score. If compatibility is low, TasteBuddy switches to conflict mode and suggests compromise options.
8. **Feedback Loop**
User interactions continuously update stored preferences and group state. This allows the system to adapt recommendations as the conversation evolves.
---

## Tech Stack

- **Language Model:** OpenAI GPT-4o-mini  
- **Backend:** Python  
- **APIs:** OPENAI API, SERPAPI Yelp API
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

#### 2. SERPAPI API Key

Create one at: [https://www.yelp.com/developers/v3/manage_app](https://serpapi.com/yelp-search-api)

Add it to backend/.env:

SERPAPI_API_KEY=your_key_here

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

This happens when SERPAPI’s Yelp Places API is slow.
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

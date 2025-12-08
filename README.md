# TasteBuddy: LLM Restaurant Assistant

TasteBuddy is a Large Language Model (LLM)-powered restaurant assistant that aims to solve the issue of picking restaurants in group settings. Unlike other solutions that use filtering, TasteBuddy hopes to understand multiple users’ chats and extracts each person's preferences, analyzes group alignment, filters out unsafe options, and recommends resturants using Yeld data and an LLM reasoning layer. TasteBuddy is built specifically for New York City dining, with safety!
---

## Features

- **Multi-User Chat**: Each user will be able to join the chat with their name. Messages are stores server-side and replayed across all conencted users. The model will read everyone's messages and generate response when tagged using @TasteBuddy.   

- **Allergen and Dietary Safety**: TasteBuddy includes a custom safety layer that analyzes each user’s allergies and dietary restrictions, then removes risky restaurants before the LLM generates recommendations.


- **Interactive Feedback Loop**  


---

## Methodology

1. **Data Collection** 
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

## References

- Brahimi, S. (2024). *AI-Powered Dining: Text Information Extraction and Machine Learning for Personalized Menu Recommendations and Food Allergy Management.* International Journal of Information Technology, 17(4), 2107–2115.  
- Mao, M. et al. (2024). *Multi-User Chat Assistant (MUCA): A Framework Using LLMs to Facilitate Group Conversations.* arXiv preprint arXiv:2401.04883.

---

## About

TasteBuddy hopes to bring inclusive and personalized recommendations to users in group settings. 
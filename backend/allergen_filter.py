# backend/allergen_filter.py
import re
import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

#instead of mapping allergy based on cuisine, we map those with the keywords only 
HIGH_RISK_CATEGORY_MAP = {
    "peanut": [], 
    "shellfish": ["seafood", "oyster bar", "crab", "lobster", "shrimp"],
    "dairy": ["ice cream", "frozen yogurt", "gelato", "cheese shops"],
    "gluten": ["bakery", "bagels", "donuts"],
}

def is_category_risky(category_text, allergies):
    """
    Rule-based check using:
    - explicit allergen words in the category text
    - clearly high-risk category types for specific allergens

    We do NOT auto-block whole cuisines like "Chinese" or "Italian",
    since those can have allergy-friendly dishes.
    """
    text = category_text.lower()

    #exact word match for allergen names
    for allergy in allergies:
        pattern = rf"\b{re.escape(allergy.lower())}\b"
        if re.search(pattern, text):
            return True

    #high-risk category types (like seafood or ice cream)
    for allergy in allergies:
        high_risk_cats = HIGH_RISK_CATEGORY_MAP.get(allergy.lower(), [])
        for hr in high_risk_cats:
            if hr in text:
                return True

    return False

def llm_risk_check(categories, allergies):
    """
    LLM-based risk check.
    Given only categories + allergen list, decide if restaurant is likely risky.
    Always returns a dict: {"risky": bool, "reason": str}.
    On error or uncertainty, we fail CLOSED (treat as risky).
    """
    prompt = f"""
You are an assistant that estimates allergen risk for restaurants.

User has the following allergens: {allergies}
Restaurant categories: {categories}

Using ONLY the information in the categories, answer:
- Is it reasonably likely that the restaurant will serve food containing ANY of the allergens?
- If you are unsure, err on the side of caution and mark it as risky.

Respond in strict JSON with these keys:
{{
  "risky": true or false,
  "reason": "short explanation of why you chose that label"
}}
    """.strip()

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a cautious allergen safety assistant. When unsure, mark restaurants as risky."
                },
                {
                    "role": "user",
                    "content": prompt
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        content = resp.choices[0].message.content
        data = json.loads(content)
        risky = bool(data.get("risky", True))  
        reason = data.get("reason", "")
        return {"risky": risky, "reason": reason}

    except Exception as e:
        return {
            "risky": True,
            "reason": f"LLM error or parsing error: {e}. Defaulting to risky."
        }


def filter_allergens(restaurants, allergies):
    """Hybrid allergen filter with rule-based + LLM fallback."""
    if not allergies:
        return restaurants

    safe = []
    #implemented two checks, one with risky one with llm_answer 
    for r in restaurants:
        categories = [c.get("title", "") for c in r.get("categories", [])]

        risky = any(is_category_risky(cat, allergies) for cat in categories)
        if risky:
            continue

        llm_answer = llm_risk_check(categories, allergies)
        if llm_answer["risky"]:
            continue

        safe.append(r)

    return safe


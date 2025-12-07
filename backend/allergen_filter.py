# backend/allergen_filter.py
import re
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# mapping cuisines with likely allergens
CUISINE_ALLERGEN_MAP = {
    "thai": ["peanut"],
    "vietnamese": ["peanut"],
    "chinese": ["soy", "shellfish"],
    "sushi": ["shellfish", "soy"],
    "japanese": ["soy"],
    "korean": ["soy", "sesame"],
    "indian": ["peanut", "cashew"],
    "middle eastern": ["sesame"],
    "mediterranean": ["sesame", "nuts", "dairy"],
    "bakery": ["gluten"],
    "italian": ["dairy"],
}

def is_category_risky(category_text, allergies):
    """Check category using simple, safe rules."""
    text = category_text.lower()

    # Direct exact word match only
    for allergy in allergies:
        # Only match full words, e.g. r"\bshellfish\b"
        if re.search(rf"\b{re.escape(allergy.lower())}\b", text):
            return True

        # Check cuisine → common allergens
        for cuisine, risks in CUISINE_ALLERGEN_MAP.items():
            if cuisine in text and allergy.lower() in risks:
                return True

    return False


def llm_risk_check(categories, allergies):
    """LLM fallback: ask model if restaurant is risky."""
    prompt = f"""
    Evaluate allergen safety.

    Allergens of concern: {allergies}
    Restaurant categories: {categories}

    Question: Based on these categories only, is this restaurant likely to contain ANY of the allergens?

    Respond in strict JSON:
    {{"risky": true/false}}
    """

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return resp.choices[0].message.content
    except:
        return False  # fail-open safe path


def filter_allergens(restaurants, allergies):
    """Hybrid allergen filter with rule-based + LLM fallback."""
    if not allergies:
        return restaurants

    safe = []

    for r in restaurants:
        title = r.get("title", "")
        categories = [c.get("title", "") for c in r.get("categories", [])]

        # First: rule-based check
        risky = any(is_category_risky(cat, allergies) for cat in categories)
        if risky:
            continue

        # Second: LLM fallback (only if rule-based is inconclusive)
        llm_answer = llm_risk_check(categories, allergies)
        if isinstance(llm_answer, str):
            import json
            llm_answer = json.loads(llm_answer)

        if llm_answer.get("risky") is True:
            continue

        safe.append(r)

    return safe

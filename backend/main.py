from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import numpy as np

from llm_engine import extract_preferences
from yelp_fetch import get_restaurants
from allergen_filter import filter_allergens
from harmony_score import compute_harmony, user_prefs, prefs_to_vec
from compromise import best_compromise_restaurant
from context_manager import update_context, get_context
from diet_filter import filter_dietary_rules

# ================== APP SETUP ==================
app = FastAPI(title="TasteBuddy MUCA Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== MUCA GROUP STATE ==================
group_state = {
    "participants": {},
    "freq": {},
    "length": {},
    "last_bot_turn": 0
}

# ================== SHARED GROUP CHAT LOG ==================
group_messages = []

# ================== BOT PERSONALITY ==================
INTROS = [
    "Here are some great picks that balance everyone’s tastes 👇",
    "Based on what everyone said, these fit best 🍽️",
    "Alright team, these spots are your best match:",
    "TasteBuddy here! I found options that work for the group 👇"
]

OUTROS = [
    "Want me to narrow this down to one top choice?",
    "I can optimize this by budget or walking distance too!",
    "Tell me if you want something more casual or fancy!"
]

# ================== INPUT MODEL ==================
class ChatInput(BaseModel):
    user_id: str
    user_name: Optional[str] = None
    message: str

@app.get("/")
def root():
    return {"status": "MUCA backend running"}

# ================== USER JOIN ==================
@app.post("/join")
def join_user(payload: dict):
    name = payload.get("name", "Unknown")

    group_messages.append({
        "sender": "system",
        "text": f"🟢 {name} joined the chat"
    })

    return {"status": "ok"}

# ================== RESET MEMORY ==================
@app.post("/reset_memory")
def reset_memory():
    global group_state, group_messages, user_prefs

    group_state["participants"].clear()
    group_state["freq"].clear()
    group_state["length"].clear()
    group_state["last_bot_turn"] = 0

    group_messages.clear()
    user_prefs.clear()

    return {"status": "memory reset"}

# ================== HISTORY ==================
@app.get("/history")
def get_history():
    return group_messages

# ================== MUCA STRATEGY ==================
def choose_strategy(state, explicit_ping):
    if explicit_ping:
        return "Direct"

    if len(user_prefs) > 1:
        harmony_vals = [compute_harmony(uid, p) for uid, p in user_prefs.items()]
        if min(harmony_vals) < 0.4:
            return "Conflict"

    avg_freq = sum(state["freq"].values()) / max(1, len(state["freq"]))
    lurkers = [u for u in state["freq"] if state["freq"][u] < 0.4 * avg_freq]

    if lurkers:
        return "Encouragement"

    if sum(state["freq"].values()) - state["last_bot_turn"] > 6:
        return "Summary"

    return "Silent"

# ================== MAIN CHAT ENDPOINT ==================
@app.post("/chat")
def chat(input: ChatInput):

    try:
        # register user
        group_state["participants"][input.user_id] = input.user_name
        group_state["freq"].setdefault(input.user_id, 0)
        group_state["length"].setdefault(input.user_id, 0)

        group_state["freq"][input.user_id] += 1
        group_state["length"][input.user_id] += len(input.message)

        update_context(input.user_id, input.message)

        # save user message
        group_messages.append({
            "sender": input.user_name or "Unknown",
            "text": input.message
        })

        msg = input.message.lower()
        explicit_ping = "@tastebuddy" in msg
        strategy = choose_strategy(group_state, explicit_ping)

        # -------- SILENT --------
        if strategy == "Silent":
            return {"reply": None}

        # -------- ENCOURAGEMENT --------
        if strategy == "Encouragement":
            avg_freq = sum(group_state["freq"].values()) / len(group_state["freq"])
            lurkers = [u for u in group_state["freq"] if group_state["freq"][u] < 0.4 * avg_freq]
            names = [group_state["participants"].get(u, "someone") for u in lurkers[:2]]

            reply = f"Hey {', '.join(names)}, we’d love your input too!"

            group_messages.append({
                "sender": "TasteBuddy",
                "text": reply,
                "harmony": None,
                "restaurants": []
            })

            return {"reply": reply}

        # -------- SUMMARY --------
        if strategy == "Summary":
            group_state["last_bot_turn"] = sum(group_state["freq"].values())
            summary = get_context(input.user_id)

            reply = "Here’s a quick group summary so far:\n" + summary

            group_messages.append({
                "sender": "TasteBuddy",
                "text": reply,
                "harmony": None,
                "restaurants": []
            })

            return {"reply": reply}

        # -------- DIRECT / CONFLICT --------
        prefs = extract_preferences(input.message)
        harmony = compute_harmony(input.user_id, prefs)

        cuisine = (prefs.get("cuisine") or ["food"])[0]
        location = prefs.get("location") or "New York City"
        allergies = prefs.get("allergies") or []

        yelp_data = get_restaurants(term=cuisine, location=location, limit=5)
        restaurants = yelp_data.get("businesses", [])

        safe_restaurants = filter_allergens(restaurants, allergies)
        ranked = safe_restaurants

        conflict_section = ""
        if strategy == "Conflict" and ranked:
            vecs = [prefs_to_vec(p) for p in user_prefs.values()]
            group_avg = np.mean(vecs, axis=0)
            best_rest, best_sim = best_compromise_restaurant(ranked, group_avg)

            conflict_section = (
                "🟦 Group conflict detected.\n"
                f"🟪 Best compromise: {best_rest.get('title')} (fit {best_sim:.2f})\n\n"
            )

        lines = [
            f"- {r.get('title')} – {r.get('rating')}★ – {r.get('price','?')}"
            for r in ranked[:5]
        ]

        core_reply = conflict_section + "\n".join(lines)

        intro = np.random.choice(INTROS)
        outro = np.random.choice(OUTROS)

        full_reply = f"{intro}\n\n{core_reply}\n\n{outro}"

        group_messages.append({
            "sender": "TasteBuddy",
            "text": full_reply,
            "harmony": harmony,
            "restaurants": ranked[:5]
        })

        return {
            "reply": full_reply,
            "harmony_score": harmony,
            "restaurants": ranked[:5]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

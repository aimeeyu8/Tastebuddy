from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import numpy as np
from .llm_engine import extract_preferences, generate_final_reply
from .yelp_fetch import get_restaurants
from .allergen_filter import filter_allergens
from .harmony_score import compute_harmony, user_prefs, prefs_to_vec
from .compromise import best_compromise_restaurant
from .context_manager import update_context, get_context
from .diet_filter import filter_dietary_rules



# ================== app setup ==================
app = FastAPI(title="TasteBuddy MUCA Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== muca group state ==================
group_state = {
    "participants": {},
    "freq": {},
    "length": {},
    "last_bot_turn": 0
}

# ================== shared group chat log ==================
group_messages = []

# ================== bot personality ==================
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

# ================== input model ==================
class ChatInput(BaseModel):
    user_id: str
    user_name: Optional[str] = None
    message: str

@app.get("/")
def root():
    return {"status": "MUCA backend running"}

# ================== user join ==================
@app.post("/join")
def join_user(payload: dict):
    name = payload.get("name", "Unknown")

    group_messages.append({
        "sender": "system",
        "text": f"{name} joined the chat"
    })

    return {"status": "ok"}

# ================== reset memory ==================
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

# ================== history ==================
@app.get("/history")
def get_history():
    return group_messages

# ================== muca strategy selector ==================
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

# ================== main chat endpoint ==================
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

        # -------- silent --------
        if strategy == "Silent":
            return {"reply": None}

        # -------- encouragement --------
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

                # -------- summary --------
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

        # -------- direct / conflict --------
        # 1) Extract preferences and update harmony
        prefs = extract_preferences(input.message)
        harmony = compute_harmony(input.user_id, prefs)

        cuisine = (prefs.get("cuisine") or ["food"])[0]
        location = prefs.get("location") or "New York City"
        allergies = prefs.get("allergies") or []

        # 2) Fetch Yelp restaurants
        yelp_data = get_restaurants(term=cuisine, location=location, limit=8)
        restaurants = yelp_data.get("businesses", [])

        # 3) Apply allergy + diet filters
        safe_restaurants = filter_allergens(restaurants, allergies)
        safe_restaurants = filter_dietary_rules(safe_restaurants, prefs)

        ranked = safe_restaurants

        # 4) If there is group conflict, compute best compromise and pass as note
        conflict_notes = {}
        if strategy == "Conflict" and ranked:
            vecs = [prefs_to_vec(p) for p in user_prefs.values()]
            group_avg = np.mean(vecs, axis=0)
            best_rest, best_sim = best_compromise_restaurant(ranked, group_avg)

            conflict_notes = {
                "conflict": True,
                "best_compromise_name": best_rest.get("title"),
                "best_compromise_fit": round(float(best_sim), 2),
            }

        # 5) Notes for the LLM-generated final reply
        notes = {
            "strategy": strategy,
            "allergies": allergies,
            "num_allergy_filtered": len(restaurants) - len(safe_restaurants),
            **conflict_notes,
        }

        # 6) Generate a friendly, human final reply using the LLM
        full_reply = generate_final_reply(
            user_query=input.message,
            prefs=prefs,
            restaurants=ranked,
            notes=notes,
        )

        # 7) Save to group history and return
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

# backend/main.py
# main.py contains the fastapi app and the chat logic including endpoints
# takes care of the flow from receiving user message -> extracting preferences -> fetching from yelp api -> filtering -> ranking -> generating final reply

from typing import Optional, List
import traceback
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .llm_engine import extract_preferences, generate_final_reply
from .yelp_fetch import yelp_search
from .allergen_filter import filter_allergens
from .diet_filter import filter_dietary_rules
from .ranking import rank_restaurants
from .harmony_score import compute_harmony, user_prefs, prefs_to_vec
from .compromise import best_compromise_restaurant
from .context_manager import update_context, reset_all_context

# Fast API app setup 
app = FastAPI(title="TasteBuddy MUCA Backend")
# allow cors for all origins so frontend can call
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# multi user chat state, tracks name, how many messages sent, length of messages, and last bot message

group_state = {
    "participants": {},
    "freq": {},
    "length": {},
    "last_bot_turn": 0,
}
# message history, frontend polls this to display chat
group_messages: List[dict] = []


# Input model for chat endpoint
class ChatInput(BaseModel):
    user_id: str
    user_name: Optional[str] = None
    message: str

# push message to history with unique ID
def push_message(sender, text, harmony=None, restaurants=None):
    msg = {
        "id": len(group_messages),
        "sender": sender,
        "text": text,
        "harmony": harmony,
        "restaurants": restaurants or [],
    }
    group_messages.append(msg)
    return msg


@app.get("/")
def root():
    return {"status": "TasteBuddy MUCA backend running"}

# app.post to join the chat, 
@app.post("/join")
def join_user(payload: dict):
    name = payload.get("name", "Unknown")
    push_message("system", f"{name} joined the chat")
    return {"status": "ok"}

# app.post to reset memory, resets chat history, group state, user preferences, and context manager
@app.post("/reset_memory")
def reset_memory():
    global group_state, group_messages, user_prefs

    group_state = {"participants": {}, "freq": {}, "length": {}, "last_bot_turn": 0}
    group_messages.clear()
    user_prefs.clear()
    reset_all_context()
    return {"status": "memory reset"}

# retrieve chat history
@app.get("/history")
def get_history():
    return group_messages


# strategy logic
def choose_strategy(state, explicit_ping: bool) -> str:
    from .harmony_score import compute_harmony_score

    # if user directly mentions tastebuddy, they will get a response
    if explicit_ping:
        return "Direct"

    # Conflict detection
    if len(user_prefs) > 1:
        scores = [
            compute_harmony_score(uid, prefs, dict(user_prefs))
            for uid, prefs in user_prefs.items()
        ]
        if scores and min(scores) < 0.4:
            return "Conflict"

    # Encouragement if some users are silent/quiet
    if state["freq"]:
        avg_freq = sum(state["freq"].values()) / len(state["freq"])
        if any(state["freq"][u] < 0.4 * avg_freq for u in state["freq"]):
            return "Encouragement"

    # Summary if there have been more than 6 messages since last bot message
    total_msgs = sum(state["freq"].values())
    if total_msgs - state["last_bot_turn"] > 6:
        return "Summary"

    return "Direct"

# main chat endpoint
@app.post("/chat")
def chat(input: ChatInput):
    # backend logs user identity, message count, totaly characters typed
    try:
        uid = input.user_id
        name = input.user_name or "Guest"

        # track user in group state
        group_state["participants"][uid] = name
        group_state["freq"].setdefault(uid, 0)
        group_state["length"].setdefault(uid, 0)
        group_state["freq"][uid] += 1
        group_state["length"][uid] += len(input.message)

        update_context(uid, input.message)

        # Record user message + adds to shared chat history
        push_message(name, input.message)

        explicit_ping = "@tastebuddy" in input.message.lower()
        strategy = choose_strategy(group_state, explicit_ping)

        # choose strategy - user will pint bot + give key word for what they want the bot to do
        if strategy == "Encouragement":
            avg_freq = sum(group_state["freq"].values()) / len(group_state["freq"])
            lurkers = [
                u for u in group_state["freq"]
                if group_state["freq"][u] < 0.4 * avg_freq
            ]
            names = [group_state["participants"].get(u, "someone") for u in lurkers[:2]]
            reply = f"Hey {', '.join(names)}, we’d love your input too!"

            push_message("TasteBuddy", reply)
            return {"reply": reply}


        # Summary Strategy, summarizes last 10 messages
        if strategy == "Summary":
            group_state["last_bot_turn"] = sum(group_state["freq"].values())
            last_msgs = group_messages[-10:]
            lines = [f"{m['sender']}: {m['text']}" for m in last_msgs]
            reply = "Here’s a quick summary so far:\n" + "\n".join(lines)

            push_message("TasteBuddy", reply)
            return {"reply": reply}


        # Direct / Conflict Strategy
        # extract user prefeerences
        prefs = extract_preferences(input.message)
        # compute user harmony which should measure how different a user's preferences are from their group
        harmony = compute_harmony(uid, prefs)

        cuisine = (prefs.get("cuisine") or ["food"])[0]
        location = prefs.get("location") or "New York City"
        allergies = prefs.get("allergies") or []
        diet_rules = prefs.get("diet") or []


        # Yelp Search, this should return normalized restaurants
        restaurants = yelp_search(term=cuisine, location=location, limit=12)

        # If Yelp returns nothing → fallback message immediately
        if not restaurants:
            fallback = (
                "I couldn’t find any places for that cuisine in this area.\n"
                "Want me to try a nearby neighborhood or expand the cuisine search?"
            )
            push_message("TasteBuddy", fallback, harmony, [])
            return {"reply": fallback, "harmony_score": harmony, "restaurants": []}

        # Allergen Filtering, if more thn 30% of menu items contain allergen, restaurant is filtered out
        safe_restaurants, allergen_debug = filter_allergens(
            restaurants,
            allergies,
            threshold=0.3,
        )

        safe_restaurants = filter_dietary_rules(safe_restaurants, diet_rules)

        # fallback: if everything filtered, relax allergen filtering
        relaxed = False
        if not safe_restaurants:
            relaxed = True
            restaurants_for_ranking = restaurants
        else:
            restaurants_for_ranking = safe_restaurants

        # Ranking, scores each restaurant by rating
        ranked = rank_restaurants(
            restaurants_for_ranking,
            prefs,
            allergen_debug=allergen_debug
        )

        # FINAL fallback: ranked empty
        if not ranked:
            fallback = (
                "I couldn’t find any places that fully match all filters.\n"
                "If you’d like, I can relax the allergy, budget, or cuisine rules and try again!"
            )
            push_message("TasteBuddy", fallback, harmony, [])
            return {"reply": fallback, "harmony_score": harmony, "restaurants": []}

        # Conflict Resolution
        conflict_notes = {}
        # if the strategy is conflict, then we compute the group-average preference vector. We then find a restaurant that is best for everyone
        if strategy == "Conflict":
            vecs = [prefs_to_vec(p) for p in user_prefs.values()]
            group_avg = np.mean(vecs, axis=0)
            best_rest, best_sim = best_compromise_restaurant(ranked, group_avg)

            if best_rest:
                conflict_notes = {
                    "conflict": True,
                    "best_compromise_name": best_rest.get("title"),
                    "best_compromise_fit": round(float(best_sim), 2),
                }

        notes = {
            "strategy": strategy,
            "allergies": allergies,
            "diet_rules": diet_rules,
            "relaxed": relaxed,
            "allergen_debug": allergen_debug,
            **conflict_notes,
        }

        # Generate Final Reply
        full_reply = generate_final_reply(
            user_query=input.message,
            prefs=prefs,
            restaurants=ranked,
            notes=notes,
        )

        # this pushes the bot message into the history
        push_message("TasteBuddy", full_reply, harmony, ranked[:5])

        # front end uses reurn response to update output
        return {
            "reply": full_reply,
            "harmony_score": harmony,
            "restaurants": ranked[:5],
        }

    except Exception as e:
        print("\n=== ERROR IN /chat ENDPOINT ===")
        traceback.print_exc()
        print("=== End ERROR ===\n")
        raise HTTPException(status_code=500, detail=str(e))
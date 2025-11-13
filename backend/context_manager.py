import json, os
os.makedirs("data", exist_ok=True)
FILE = "data/conversation_memory.json"

if not os.path.exists(FILE):
    json.dump({}, open(FILE, "w"))

memory = json.load(open(FILE))

def update_context(user_id: str, message: str):
    if user_id not in memory:
        memory[user_id] = []
    memory[user_id].append(message)
    json.dump(memory, open(FILE, "w"), indent=2)

def get_context(user_id: str):
    return memory.get(user_id, [])
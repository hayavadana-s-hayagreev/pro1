import json
from pathlib import Path
from datetime import datetime

HISTORY_FILE = Path("data/user_history.json")

def load_history():
    if not HISTORY_FILE.exists():
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        return {"searches": [], "predictions": []}
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def add_prediction(username: str, data: dict):
    history = load_history()
    entry = {
        "id": str(datetime.now().timestamp()),
        "username": username,
        "timestamp": datetime.now().isoformat(),
        "type": "prediction",
        "data": data
    }
    history["predictions"].insert(0, entry)
    # Keep only last 100
    history["predictions"] = history["predictions"][:100]
    save_history(history)
    return entry

def add_search(username: str, query: str):
    history = load_history()
    entry = {
        "id": str(datetime.now().timestamp()),
        "username": username,
        "timestamp": datetime.now().isoformat(),
        "type": "search",
        "query": query
    }
    history["searches"].insert(0, entry)
    history["searches"] = history["searches"][:100]
    save_history(history)
    return entry

def get_user_history(username: str):
    history = load_history()
    user_preds = [p for p in history["predictions"] if p["username"] == username]
    user_searches = [s for s in history["searches"] if s["username"] == username]
    return {
        "predictions": user_preds,
        "searches": user_searches
    }

from pathlib import Path
import json
import re
import shutil


ROOT_DIR = Path(__file__).resolve().parents[1]
CONTEXT_FILE = ROOT_DIR / "memory" / "chat_history.json"


def safe_user_key(name):
    key = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip()
    return key or "unknown"


def load_all_contexts():
    if not CONTEXT_FILE.exists():
        return {}

    try:
        with CONTEXT_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        backup_path = CONTEXT_FILE.with_suffix(".json.bak")
        shutil.copyfile(CONTEXT_FILE, backup_path)
        return {}


def save_all_contexts(contexts):
    CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_path = CONTEXT_FILE.with_suffix(".json.tmp")

    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(contexts, file, ensure_ascii=False, indent=2)

    temp_path.replace(CONTEXT_FILE)


def get_history(user_name, max_messages):
    contexts = load_all_contexts()
    history = contexts.get(safe_user_key(user_name), [])
    if not isinstance(history, list):
        return []

    return history[-max_messages:]


def append_exchange(user_name, user_message, assistant_message, max_messages):
    contexts = load_all_contexts()
    user_key = safe_user_key(user_name)
    history = contexts.get(user_key, [])

    if not isinstance(history, list):
        history = []

    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": assistant_message})
    overflow_messages = history[:-max_messages] if len(history) > max_messages else []
    contexts[user_key] = history[-max_messages:]

    save_all_contexts(contexts)
    return overflow_messages

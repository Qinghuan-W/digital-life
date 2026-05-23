from datetime import datetime
from pathlib import Path
import json

from services.context_store import safe_user_key


ROOT_DIR = Path(__file__).resolve().parents[1]
LONG_TERM_DIR = ROOT_DIR / "memory" / "long_term"
PROFILE_FIELDS = {
    "name": "",
    "nicknames": [],
    "likes": [],
    "dislikes": [],
    "important_facts": [],
    "boundaries": [],
}


def get_user_memory_dir(user_name):
    user_dir = LONG_TERM_DIR / safe_user_key(user_name)
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def get_summary_path(user_name):
    return get_user_memory_dir(user_name) / "summary.md"


def get_pending_path(user_name):
    return get_user_memory_dir(user_name) / "pending.json"


def get_profile_path(user_name):
    return get_user_memory_dir(user_name) / "profile.json"


def normalize_profile(profile):
    normalized = {}
    profile = profile if isinstance(profile, dict) else {}

    for field, default_value in PROFILE_FIELDS.items():
        value = profile.get(field, default_value)
        if isinstance(default_value, list):
            if not isinstance(value, list):
                value = []
            normalized[field] = [
                str(item).strip()
                for item in value
                if str(item).strip()
            ]
        else:
            normalized[field] = str(value or "").strip()

    updated_at = str(profile.get("updated_at", "") or "").strip()
    if updated_at:
        normalized["updated_at"] = updated_at

    return normalized


def load_core_profile(user_name):
    profile_path = get_profile_path(user_name)
    if not profile_path.exists():
        return normalize_profile({})

    try:
        data = json.loads(profile_path.read_text(encoding="utf-8"))
        return normalize_profile(data)
    except json.JSONDecodeError:
        backup_path = profile_path.with_suffix(".json.bak")
        profile_path.replace(backup_path)
        return normalize_profile({})


def save_core_profile(user_name, profile):
    profile = normalize_profile(profile)
    profile["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    profile_path = get_profile_path(user_name)
    profile_path.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def format_core_profile(profile):
    profile = normalize_profile(profile)
    lines = []

    if profile["name"]:
        lines.append(f"- 用户名字：{profile['name']}")
    if profile["nicknames"]:
        lines.append(f"- 可用称呼：{'、'.join(profile['nicknames'])}")
    if profile["likes"]:
        lines.append(f"- 喜欢：{'、'.join(profile['likes'])}")
    if profile["dislikes"]:
        lines.append(f"- 不喜欢：{'、'.join(profile['dislikes'])}")
    if profile["important_facts"]:
        lines.append(f"- 重要事实：{'；'.join(profile['important_facts'])}")
    if profile["boundaries"]:
        lines.append(f"- 边界/禁忌：{'；'.join(profile['boundaries'])}")

    return "\n".join(lines)


def load_long_term_memory(user_name):
    summary_path = get_summary_path(user_name)
    if not summary_path.exists():
        return ""

    return summary_path.read_text(encoding="utf-8").strip()


def load_memory_context(user_name, max_pending_messages=20):
    core_profile = format_core_profile(load_core_profile(user_name))
    summary = load_long_term_memory(user_name)
    pending_messages = load_pending_messages(user_name)

    sections = []
    if core_profile:
        sections.append(f"【核心资料，优先级最高】\n{core_profile}")

    if summary:
        sections.append(f"【长期总结】\n{summary}")

    if pending_messages:
        if max_pending_messages > 0:
            pending_messages = pending_messages[-max_pending_messages:]

        pending_text = format_pending_messages(pending_messages)
        if pending_text:
            sections.append(f"【尚未总结的较早聊天】\n{pending_text}")

    return "\n\n".join(sections)


def get_memory_status(user_name):
    return {
        "has_profile": bool(format_core_profile(load_core_profile(user_name))),
        "has_summary": bool(load_long_term_memory(user_name)),
        "pending_count": len(load_pending_messages(user_name)),
    }


def save_long_term_memory(user_name, summary):
    summary_path = get_summary_path(user_name)
    summary_path.write_text(summary.strip() + "\n", encoding="utf-8")


def load_pending_messages(user_name):
    pending_path = get_pending_path(user_name)
    if not pending_path.exists():
        return []

    try:
        data = json.loads(pending_path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        backup_path = pending_path.with_suffix(".json.bak")
        pending_path.replace(backup_path)
        return []


def save_pending_messages(user_name, messages):
    pending_path = get_pending_path(user_name)
    pending_path.write_text(
        json.dumps(messages, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def clear_pending_messages(user_name):
    pending_path = get_pending_path(user_name)
    if pending_path.exists():
        pending_path.unlink()


def archive_overflow_messages(user_name, messages):
    if not messages:
        return 0

    archived_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pending_messages = load_pending_messages(user_name)
    added_count = 0

    for message in messages:
        role = message.get("role", "")
        content = str(message.get("content", "")).strip()
        if not role or not content:
            continue

        pending_messages.append(
            {
                "archived_at": archived_at,
                "role": role,
                "content": content,
            }
        )
        added_count += 1

    save_pending_messages(user_name, pending_messages)
    return added_count


def format_pending_messages(messages):
    lines = []
    for message in messages:
        role = message.get("role")
        label = "用户" if role == "user" else "你"
        content = str(message.get("content", "")).strip()
        if content:
            lines.append(f"{label}: {content}")
    return "\n".join(lines)

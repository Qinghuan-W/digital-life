from pathlib import Path
import os
import json
import re

from dotenv import load_dotenv
from openai import OpenAI
import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_config():
    config_path = ROOT_DIR / "config.yaml"
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_prompt(prompt_file):
    prompt_path = ROOT_DIR / prompt_file
    with prompt_path.open("r", encoding="utf-8") as file:
        return file.read().strip()


def create_client(llm_config):
    load_dotenv(ROOT_DIR / ".env")

    api_key_env = llm_config.get("api_key_env", "OPENAI_API_KEY")
    api_key = os.getenv(api_key_env)
    if not api_key:
        raise RuntimeError(
            f"没有找到环境变量 {api_key_env}。请复制 .env.example 为 .env，"
            f"然后把你的 API Key 填进去。"
        )

    client_kwargs = {"api_key": api_key}
    base_url = llm_config.get("base_url")
    if base_url:
        client_kwargs["base_url"] = base_url

    return OpenAI(**client_kwargs)


def extract_json_object(text):
    if not text:
        return "{}"

    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue

        try:
            data, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue

        if isinstance(data, dict):
            return json.dumps(data, ensure_ascii=False)

    return "{}"


def classify_reply_timing(user_message, history=None):
    config = load_config()
    llm_config = config["llm"]
    timing_config = config.get("reply_timing", {})

    profile_seconds = timing_config.get("profile_seconds", {})
    default_profile = timing_config.get("default_profile", "normal")
    fallback_delay = float(profile_seconds.get(default_profile, 4))

    if not timing_config.get("enabled", True):
        return {
            "profile": "disabled",
            "delay_seconds": 0,
            "reason": "回复时机分析已关闭",
        }

    history = history or []
    recent_context = []
    for item in history[-6:]:
        role = item.get("role")
        label = "用户" if role == "user" else "你"
        content = str(item.get("content", "")).strip()
        if content:
            recent_context.append(f"{label}: {content}")

    profiles_text = "\n".join(
        f"- {profile}: {seconds}秒"
        for profile, seconds in profile_seconds.items()
    )

    prompt = f"""
你要判断用户最新这条微信消息的情绪/关系氛围，并选择一个回复时机分类。

可选分类和对应等待时间：
{profiles_text}

分类含义：
- urgent：用户明显着急、求助、需要立刻回应
- normal：普通闲聊、普通问题
- happy：轻松开心、分享好事
- sad：低落、委屈、难受、需要安慰
- affectionate：撒娇、暧昧、表达想念或亲密
- awkward：尴尬、试探、不知道怎么接
- complex：复杂问题、长消息、需要认真想
- offended：用户冒犯、挑衅、攻击、冷嘲热讽，角色可能会不开心或需要冷静一下

最近上下文：
{chr(10).join(recent_context) if recent_context else "无"}

用户最新消息：
{user_message}

请只返回 JSON，不要解释，不要使用 Markdown：
{{"profile": "normal", "reason": "一句很短的中文原因"}}
"""

    try:
        client = create_client(llm_config)
        response = client.chat.completions.create(
            model=llm_config["model"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=120,
        )
        raw_content = response.choices[0].message.content or "{}"
        data = json.loads(extract_json_object(raw_content))

        profile = str(data.get("profile", default_profile)).strip()
        if profile not in profile_seconds:
            profile = default_profile

        min_delay = float(timing_config.get("min_delay_seconds", 0))
        max_delay = float(timing_config.get("max_delay_seconds", 30))
        delay_seconds = float(profile_seconds.get(profile, fallback_delay))
        delay_seconds = max(min_delay, min(max_delay, delay_seconds))

        return {
            "profile": profile,
            "delay_seconds": delay_seconds,
            "reason": str(data.get("reason", "")).strip(),
        }
    except Exception as error:
        return {
            "profile": default_profile,
            "delay_seconds": fallback_delay,
            "reason": f"回复时机分析失败，使用默认值：{error}",
        }


def summarize_long_term_memory(existing_memory, pending_text):
    config = load_config()
    llm_config = config["llm"]

    prompt = f"""
你要把一段微信聊天内容整理成长期记忆。

已有长期记忆：
{existing_memory if existing_memory else "暂无"}

新的待总结聊天：
{pending_text}

请输出一份更新后的长期记忆，要求：
- 用中文
- 只保留长期有用的信息、偏好、关系状态、重要事件、禁忌和承诺
- 删除寒暄、重复内容、临时小事
- 不要编造
- 使用项目符号
- 控制在 800 字以内
"""

    client = create_client(llm_config)
    response = client.chat.completions.create(
        model=llm_config["model"],
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=900,
    )
    return (response.choices[0].message.content or "").strip()


def update_core_profile(existing_profile, user_message, assistant_message, history=None):
    config = load_config()
    llm_config = config["llm"]
    history = history or []

    recent_context = []
    for item in history[-6:]:
        role = item.get("role")
        label = "用户" if role == "user" else "你"
        content = str(item.get("content", "")).strip()
        if content:
            recent_context.append(f"{label}: {content}")

    prompt = f"""
你要判断用户这次聊天里是否出现了值得长期保存的核心资料，并维护 profile.json。

核心资料只保存稳定、以后还会用到的信息。不要保存普通寒暄、临时情绪、一次性小事。

当前 profile：
{json.dumps(existing_profile or {}, ensure_ascii=False, indent=2)}

最近上下文：
{chr(10).join(recent_context) if recent_context else "无"}

用户最新消息：
{user_message}

你的回复：
{assistant_message}

请只返回 JSON，不要解释，不要 Markdown。
返回格式必须是：
{{
  "should_update": true,
  "reason": "一句很短的中文原因",
  "profile": {{
    "name": "用户真实名字或常用名字，不知道就留空字符串",
    "nicknames": ["用户希望被怎样称呼"],
    "likes": ["稳定喜好"],
    "dislikes": ["稳定不喜欢"],
    "important_facts": ["长期重要事实"],
    "boundaries": ["边界、禁忌、不要做的事"]
  }}
}}

规则：
- 如果没有新资料，should_update 必须是 false，profile 原样返回当前 profile
- 新旧信息冲突时，以用户最新明确表达为准
- 不要编造
- 列表去重
- 所有内容用中文

什么应该保存：
- 名字、昵称、希望被怎样称呼
- 稳定喜好，例如“最近迷上冰美式了”“火锅我能连吃三天”
- 稳定反感或禁忌，例如“香菜这东西我是真吃不了”“以后别叫我老师”
- 长期习惯、身份、关系状态、重要事实

什么不应该保存：
- “我今天吃了火锅”这种一次性日常
- “现在有点累”这种临时状态
- 玩笑、反问、随口一说
- 你自己的回复内容，除非用户明确确认
"""

    client = create_client(llm_config)
    response = client.chat.completions.create(
        model=llm_config["model"],
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=700,
    )

    raw_content = response.choices[0].message.content or "{}"
    data = json.loads(extract_json_object(raw_content))

    if "profile" in data:
        return data

    return {
        "should_update": True,
        "reason": "模型返回了旧格式资料",
        "profile": data,
    }


def chat_once(
    user_message,
    prompt_file=None,
    history=None,
    long_term_memory=None,
    runtime_context=None,
):
    config = load_config()
    llm_config = config["llm"]
    prompt_file = prompt_file or config["bot"]["prompt_file"]
    history = history or []

    system_prompt = load_prompt(prompt_file)
    if long_term_memory:
        system_prompt = (
            f"{system_prompt}\n\n"
            "以下是你需要参考的核心资料、长期记忆和较早聊天记录。"
            "核心资料优先级最高，里面的名字、称呼、偏好和边界不要随意忽略。"
            "其中“尚未总结的较早聊天”也是真实发生过的旧聊天，回复时要一起参考：\n"
            f"{long_term_memory}"
        )
    if runtime_context:
        system_prompt = (
            f"{system_prompt}\n\n"
            "以下是本次回复的运行时上下文。"
            "它不是长期记忆，但回答时间、日期、今天、明天、昨天、星期相关问题时必须以这里为准：\n"
            f"{runtime_context}"
        )

    client = create_client(llm_config)
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=llm_config["model"],
        messages=messages,
        temperature=float(llm_config.get("temperature", 0.9)),
        max_tokens=int(llm_config.get("max_tokens", 800)),
    )

    content = response.choices[0].message.content or ""
    return content.strip()

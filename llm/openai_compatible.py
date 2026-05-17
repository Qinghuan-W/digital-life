from pathlib import Path
import os

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


def chat_once(user_message, prompt_file=None):
    config = load_config()
    llm_config = config["llm"]
    prompt_file = prompt_file or config["bot"]["prompt_file"]

    system_prompt = load_prompt(prompt_file)
    client = create_client(llm_config)

    response = client.chat.completions.create(
        model=llm_config["model"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=float(llm_config.get("temperature", 0.9)),
        max_tokens=int(llm_config.get("max_tokens", 800)),
    )

    content = response.choices[0].message.content or ""
    return content.strip()

# **DigitalLife**

![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Windows](https://img.shields.io/badge/windows-PC%20WeChat-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![OpenAI Compatible](https://img.shields.io/badge/OpenAI--Compatible-API-412991?style=for-the-badge&logo=openai&logoColor=white)
![Status](https://img.shields.io/badge/status-early%20prototype-orange?style=for-the-badge)

## **Table of Contents**

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Implementation Details](#implementation-details)
- [Developer Instructions](#developer-instructions)
- [Memory System](#memory-system)
- [Configuration](#configuration)
- [Privacy and Safety](#privacy-and-safety)
- [Roadmap](#roadmap)

## **Overview**

DigitalLife is a personal WeChat auto-reply experiment based on Windows PC WeChat automation and OpenAI-compatible model APIs.<br>
The project aims to gradually build a small "digital life" style chat companion with personality prompts, short-term context, long-term memory and human-like reply timing.<br>

At the current stage, the project can listen to a configured WeChat chat, call a model to generate replies, remember recent conversation context, summarize older messages into long-term memory, and reply with a delay based on the emotional tone of the message.

> [!NOTE]
> This is an early local prototype. It is designed for personal learning and testing, not production deployment.

## **Features**

### Core

* Connects to Windows PC WeChat through `wxauto`.
* Listens to configured WeChat contacts or chats.
* Calls an OpenAI-compatible chat completion API to generate replies.
* Supports configurable model endpoint, model name, temperature and token limit.
* Supports persona prompts through Markdown prompt files.
* Maintains short-term conversation context.
* Stores older context into a long-term memory pipeline.
* References short-term history, pending memory and summarized memory when replying.
* Supports emotion-based reply timing.
* Supports splitting one model reply into multiple WeChat messages.
* Drains cached startup messages to reduce accidental replies to old messages.

### Additional Features

* Includes standalone model test script.
* Includes standalone WeChat send and listen test scripts.
* Keeps private memory and API keys out of GitHub through `.gitignore`.
* Provides a simple YAML-based configuration system.

## **Architecture**

```text
WeChat PC Client
      |
      v
wxauto UI Automation
      |
      v
main.py
  |-- listens for new messages
  |-- queues messages briefly
  |-- loads recent and long-term memory
  |-- asks the model for reply timing
  |-- asks the model for the actual reply
  |-- sends reply back to WeChat
      |
      v
OpenAI-compatible Model API
```

Memory flow:

```text
New conversation
      |
      v
memory/chat_history.json
      |
      |  when recent history is over the configured limit
      v
memory/long_term/<contact>/pending.json
      |
      |  when pending messages reach the summarize threshold
      v
memory/long_term/<contact>/summary.md
```

## **Project Structure**

```text
DigitalLife/
|-- README.md                         # Project overview and setup instructions
|-- config.yaml                       # Main project configuration
|-- requirements.txt                  # Python dependencies
|-- .env.example                      # Environment variable example
|-- .gitignore                        # Files ignored by Git
|
|-- main.py                           # Main WeChat auto-reply loop
|-- test_ai.py                        # Model API test script
|-- test_wx.py                        # WeChat send test script
|-- test_listen.py                    # WeChat listen test script
|
|-- llm/
|   |-- __init__.py
|   `-- openai_compatible.py          # Model calls, timing analysis and memory summarization
|
|-- prompts/
|   `-- default.md                    # Default persona prompt
|
|-- services/
|   |-- __init__.py
|   |-- context_store.py              # Short-term context storage
|   `-- long_term_memory.py           # Long-term memory storage
|
`-- memory/                           # Runtime memory, ignored by Git
    |-- chat_history.json
    `-- long_term/
        `-- <contact>/
            |-- pending.json
            `-- summary.md
```

> [!IMPORTANT]
> The `memory/` folder is generated at runtime and is intentionally ignored by Git because it may contain private chat data.

## **Implementation Details**

| Technology | Usage |
|---|---|
| Python | Main programming language. |
| wxauto | Controls Windows PC WeChat through UI automation. |
| OpenAI Python SDK | Calls OpenAI-compatible model APIs. |
| python-dotenv | Loads local API keys from `.env`. |
| PyYAML | Reads project configuration from `config.yaml`. |
| Markdown prompts | Defines the bot persona and reply style. |
| JSON files | Stores short-term and pending memory locally. |
| Markdown memory | Stores summarized long-term memory in `summary.md`. |

## **Developer Instructions**

### Prerequisites

Before you begin, make sure you have:

- **Windows**
- **Python 3.10+**
- **Windows PC WeChat**, already logged in
- **An OpenAI-compatible model API key**

### Local Setup

#### 1. Clone the Repository

```powershell
git clone https://github.com/Qinghuan-W/digital-life.git
cd digital-life
```

#### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

#### 3. Create Environment File

```powershell
copy .env.example .env
```

Then edit `.env`:

```env
DEEPSEEK_API_KEY=sk-your-key-here
```

Do not commit `.env` to GitHub.

#### 4. Configure Model and WeChat Contact

Open `config.yaml` and update the model section:

```yaml
llm:
  provider: openai-compatible
  base_url: https://your-api-endpoint/v1
  model: your-model-name
  api_key_env: DEEPSEEK_API_KEY
  temperature: 0.9
  max_tokens: 800
```

Then update the WeChat contact:

```yaml
wechat:
  contacts:
    - name: Your WeChat Remark Name
      enabled: true
      prompt_file: prompts/default.md
```

The `name` should match the WeChat remark name, group name or chat title as closely as possible.

#### 5. Test the Model API

```powershell
python test_ai.py
```

#### 6. Run the Bot

```powershell
python main.py
```

To stop the program:

```text
Ctrl + C
```

## **Memory System**

DigitalLife currently uses three layers of memory.

| Memory Layer | File | Purpose |
|---|---|---|
| Short-term memory | `memory/chat_history.json` | Keeps the most recent conversation messages. |
| Pending memory | `memory/long_term/<contact>/pending.json` | Stores older messages that have not been summarized yet. |
| Long-term summary | `memory/long_term/<contact>/summary.md` | Stores summarized long-term memory. |

Current memory logic:

1. New messages are stored in `chat_history.json`.
2. When short-term history exceeds `max_history_messages`, older messages move into `pending.json`.
3. When `pending.json` reaches `summarize_overflow_after_messages`, the model summarizes it into `summary.md`.
4. After summary succeeds, `pending.json` is deleted.
5. Every reply can reference `chat_history.json`, `pending.json` and `summary.md`.

This means pending memory is still used for replies before it becomes a long-term summary.

## **Configuration**

### Memory Configuration

```yaml
bot:
  max_history_messages: 10

memory:
  enable_long_term_memory: true
  summarize_overflow_after_messages: 20
  max_pending_messages_for_reply: 20
```

| Field | Meaning |
|---|---|
| `max_history_messages` | Number of recent messages kept as short-term context. |
| `summarize_overflow_after_messages` | Number of pending messages required before summarization. |
| `max_pending_messages_for_reply` | Maximum pending messages included when generating replies. |

### Reply Timing Configuration

```yaml
reply_timing:
  enabled: true
  default_profile: normal
  min_delay_seconds: 0
  max_delay_seconds: 30
  profile_seconds:
    urgent: 1
    normal: 4
    happy: 3
    sad: 7
    affectionate: 6
    awkward: 8
    complex: 10
    offended: 16
```

The model first classifies the emotional tone of the incoming message, then chooses a reply delay profile.

### Prompt Configuration

The default persona prompt is stored in:

```text
prompts/default.md
```

If a model reply should be split into multiple WeChat messages, the prompt can instruct the model to use a backslash:

```text
今天辛苦啦\先休息一下
```

The program will send this as two separate messages.

## **Privacy and Safety**

The following files are ignored by Git:

```text
.env
memory/
```

- `.env` contains private API keys.
- `memory/` contains private conversation history and long-term memory.

If an API key is accidentally committed to a public repository, revoke it immediately and create a new one.

> [!WARNING]
> This project uses desktop UI automation for WeChat. It is not an official WeChat API integration. Use it only for personal experiments and be careful with account safety, privacy and platform rules.

## **Roadmap**

Planned improvements:

* Add `profile.json` core memory for stable facts such as name, nickname, preferences and boundaries.
* Add a dashboard for managing contacts, model settings and memory.
* Improve multi-contact support.
* Add memory view, clear and manual edit commands.
* Improve time awareness for questions such as "what time is it now".
* Add better error handling around WeChat UI automation.
* Add safer testing tools for memory behavior.

# DigitalLife

一个基于 Windows 电脑版微信自动化和 OpenAI-compatible 模型接口的个人微信自动回复实验项目。

目前这个项目还处在早期阶段，目标是逐步做成一个带有短期上下文、长期记忆、人格提示词和可配置回复节奏的“数字生命”聊天助手。

## 当前功能

- 通过 `wxauto` 连接 Windows 电脑版微信
- 监听指定微信聊天对象
- 调用 OpenAI-compatible 接口生成回复
- 支持在 `config.yaml` 中切换模型、接口地址和回复参数
- 支持短期上下文记忆
- 支持长期记忆：
  - 最近消息保存在 `memory/chat_history.json`
  - 超出短期上限的旧消息进入 `pending.json`
  - `pending.json` 达到阈值后自动总结进 `summary.md`
  - 每次回复时会同时参考短期上下文、待总结记忆和长期总结
- 支持根据用户消息情绪判断回复等待时间
- 支持多段微信消息发送
- 支持启动时忽略微信缓存旧消息，减少重复回复历史消息的问题

## 当前限制

- 目前主要在 Windows + 电脑版微信环境测试
- 依赖微信桌面端 UI 自动化，不是微信官方 API
- 运行时需要保持微信客户端在线，并尽量不要频繁切换窗口状态
- 长期记忆目前是第一版，仍可能出现总结遗漏，后续计划加入更稳定的核心记忆
- 暂时没有 dashboard，配置主要通过 `config.yaml` 和 `.env` 修改

## 环境要求

- Windows
- Python 3.10 或更高版本，当前开发环境为 Python 3.11
- 已登录的 Windows 电脑版微信
- 一个兼容 OpenAI Chat Completions 格式的模型接口

## 安装

克隆项目后进入目录：

```powershell
cd C:\Users\你的用户名\Desktop\DigitalLife
```

安装依赖：

```powershell
pip install -r requirements.txt
```

复制环境变量文件：

```powershell
copy .env.example .env
```

然后编辑 `.env`，填入你的 API Key：

```env
DEEPSEEK_API_KEY=sk-your-key-here
```

注意：`.env` 不要提交到 GitHub。

## 配置

主要配置文件是 `config.yaml`。

模型配置示例：

```yaml
llm:
  provider: openai-compatible
  base_url: https://example.com/v1
  model: your-model-name
  api_key_env: DEEPSEEK_API_KEY
  temperature: 0.9
  max_tokens: 800
```

微信监听对象配置示例：

```yaml
wechat:
  contacts:
    - name: 你的微信备注名
      enabled: true
      prompt_file: prompts/default.md
```

这里的 `name` 要和微信里的备注名、群名或聊天名尽量保持一致。

记忆配置示例：

```yaml
bot:
  max_history_messages: 10

memory:
  enable_long_term_memory: true
  summarize_overflow_after_messages: 20
  max_pending_messages_for_reply: 20
```

含义：

- `max_history_messages`: 短期上下文保留最近多少条消息
- `summarize_overflow_after_messages`: `pending.json` 累计多少条后触发长期总结
- `max_pending_messages_for_reply`: 回复时最多参考多少条未总结旧消息

## 运行

先测试模型是否能正常调用：

```powershell
python test_ai.py
```

如果模型测试正常，再运行主程序：

```powershell
python main.py
```

程序启动后会：

1. 连接微信
2. 切换到配置里的聊天对象
3. 开始监听新消息
4. 收到消息后调用模型生成回复
5. 自动发送到微信

退出程序可以按：

```text
Ctrl + C
```

## 记忆机制

项目运行后会自动生成 `memory/` 文件夹。这个文件夹不会提交到 GitHub，因为里面可能包含私人聊天内容。

当前记忆流程：

```text
最近消息
  -> memory/chat_history.json

超出短期上限的旧消息
  -> memory/long_term/联系人名/pending.json

pending.json 达到阈值
  -> 调用模型总结
  -> memory/long_term/联系人名/summary.md
  -> 删除 pending.json
```

每次生成回复时，模型会参考：

```text
chat_history.json
pending.json
summary.md
```

所以即使旧消息还没有被总结进 `summary.md`，只要它还在 `pending.json` 中，也会参与回复。

## 提示词

默认人格提示词在：

```text
prompts/default.md
```

你可以在这里调整回复风格、说话习惯和分段规则。

如果想让一句回复拆成多条微信消息，可以让模型用反斜线分隔：

```text
今天辛苦啦\先休息一会儿
```

程序会把它拆成两条微信消息发送。

## 文件说明

```text
main.py                         主程序，负责微信监听、消息队列、回复发送
config.yaml                     项目配置
requirements.txt                Python 依赖
.env.example                    环境变量示例
prompts/default.md              默认人格提示词
llm/openai_compatible.py        模型调用、回复时机分析、长期总结
services/context_store.py       短期上下文存储
services/long_term_memory.py    长期记忆存储
test_ai.py                      模型调用测试
test_wx.py                      微信发送测试
test_listen.py                  微信监听测试
```

## 隐私与安全

以下内容不会提交到 GitHub：

```text
.env
memory/
```

`.env` 保存 API Key，`memory/` 保存聊天记忆和长期总结，都属于私人数据。

如果误把 API Key 暴露到公开仓库，应立即删除并重新生成新的 Key。

## 后续计划

- 增加 `profile.json` 核心记忆，用来稳定保存昵称、姓名、偏好、禁忌等不该丢的信息
- 增加 dashboard，用网页界面管理监听对象、模型配置和记忆
- 支持更清晰的多联系人配置
- 增加记忆查看、清空和手动编辑功能
- 优化回复时机判断和上下文压缩策略

## 声明

本项目仅用于个人学习和本地实验。微信自动化依赖桌面端 UI 操作，使用时请注意账号安全、隐私保护和平台规则。

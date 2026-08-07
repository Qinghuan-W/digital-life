# LLM Provider 兼容配置

DigitalLife 的业务层只依赖统一 `LLMProvider`。具体 OpenAI-compatible 端点必须显式配置：

```dotenv
LLM_API_MODE=responses
LLM_JSON_MODE_ENABLED=true
LLM_STRUCTURED_OUTPUT_ENABLED=true
```

- `responses` 调用 Responses API；Structured Outputs 不兼容时由开发者关闭对应开关。
- `chat_completions` 调用 Chat Completions；`response_format` 不兼容时由开发者关闭 JSON Mode。
- 关闭结构化参数后，Prompt 仍要求严格 JSON，后端继续统一解析和校验。
- 模型别名本身不能证明支持某个端点。代码不会按名称或 Base URL 建立供应商分支。
- timeout、连接中断、429、5xx 或格式错误都不会触发端点切换或第二次模型调用。

两个 adapter 都返回 `GeneratedAssistantTurn`：1～4 条独立消息和一个仅用于本轮展示节奏的 `conversation_signal`。JSON 无法解析时完整文本降级成单气泡，不按标点拆分。Provider 错误对移动端统一为安全 503；开发日志只保留脱敏元数据。

旧版微信机器人仅作为产品节奏参考。新 App 没有复制或运行 wxauto、微信发送逻辑、聊天记录、记忆文件、私人配置或密钥，也没有引入聊天记录上传、风格提取、长期记忆或 Agent 工具。

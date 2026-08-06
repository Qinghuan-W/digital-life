# Persona 与基础聊天 API

Phase 2 在现有认证系统上增加 Persona、默认对话、消息持久化和非流式 LLM 回复。所有接口使用 `/api/v1` 前缀并要求 `Authorization: Bearer <access_token>`。

## 数据模型

- `personas`：归属用户，保存显示名、关系、可选年龄、性别、描述和头像 URL。
- `conversations`：归属用户并关联一个 Persona；Phase 2 中每个 Persona 只有一个默认对话。
- `messages`：归属对话，角色为 `user` 或 `assistant`，保存内容、状态和时间。
- 用户消息的 `(conversation_id, client_message_id)` 唯一，保证客户端重试不会重复保存。
- Assistant 消息通过内部 `reply_to_message_id` 唯一关联用户消息，避免并发重试生成重复回复。

删除用户会级联删除其 Persona、对话和消息。表结构只由 Alembic migration 管理。

## 接口

### 创建 Persona 与默认对话

`POST /api/v1/personas`，成功返回 `201`。

```json
{
  "display_name": "小雨",
  "relationship_label": "朋友",
  "age": 22,
  "gender_label": "女",
  "description": "大学时期认识的朋友"
}
```

响应同时包含 `persona` 和 `conversation`。后端在同一事务中创建两者，默认对话标题等于 `display_name`；任一步失败都会回滚。

### Persona 列表

`GET /api/v1/personas` 返回当前用户自己的 Persona。

### 首页对话列表

`GET /api/v1/conversations` 返回当前用户自己的对话。包含 Persona 摘要、最近消息角色、最多 100 字的预览和时间。有消息的对话按 `last_message_at` 倒序，其余按创建时间倒序；查询使用相关子查询获取最近消息，避免逐项查询。

### 对话详情

`GET /api/v1/conversations/{conversation_id}` 返回对话及 Persona 基础资料。

### 消息历史

`GET /api/v1/conversations/{conversation_id}/messages?limit=50&before=<ISO-8601>` 返回按创建时间正序排列的消息。`limit` 范围为 1–100，`before` 可用于向前分页。

### 发送消息

`POST /api/v1/conversations/{conversation_id}/messages`。

```json
{
  "content": "你好",
  "client_message_id": "8f0d37b6-f1c0-4c39-bf94-e89a785391ac"
}
```

`content` 会去除首尾空格，不能为空且最长 4000 字符。成功响应包含 `user_message` 和 `assistant_message`。本阶段是普通非流式响应，不提供 SSE、WebSocket、停止生成或重新生成。

## 用户隔离与错误

所有读取和写入都以当前登录用户为边界。访问其他用户的 Persona 或 Conversation 统一返回 `404 conversation_not_found`，避免泄露资源是否存在。

可预期错误沿用统一结构：

```json
{
  "error": "ai_service_unavailable",
  "message": "AI 服务暂时不可用，请稍后重试。"
}
```

LLM 失败时，用户消息会保留，Assistant 消息不会伪造，API 返回 `503`。移动端保留失败消息并以相同 `client_message_id` 重试。

## 消息幂等与事务边界

1. 后端先按 `client_message_id` 查找已有用户消息。
2. 首次请求单独提交用户消息，然后读取最近上下文。
3. LLM 网络调用期间不持有数据库事务或行锁。
4. 成功后保存 Assistant 消息并更新对话时间。
5. 重试复用已有用户消息；数据库唯一约束处理并发竞争。

因此网络失败不会丢失用户消息，也不会因重复点击插入多条相同消息。

## LLM Provider 架构

```text
FastAPI Route
  -> ChatService
  -> LLMProvider protocol
  -> OpenAIProvider
  -> OpenAI Responses API
```

`ChatService` 只依赖 Provider 接口。正式运行使用 OpenAI Provider；测试注入 Fake Provider，测试不会访问外部网络。配置来自后端环境变量：

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_BASE_URL`（可空）
- `LLM_TIMEOUT_SECONDS`
- `LLM_HISTORY_LIMIT`

真实 API Key 只允许写入未被 Git 跟踪的 `backend/.env`，不得进入移动端、文档、日志、测试或 Git 历史。供应商错误、请求地址和堆栈不会返回客户端。

## Prompt 当前边界

当前 Prompt Builder 使用固定通用系统提示，明确回复者是 AI，不声称是真实人物、现实身体、位置或即时经历，也不冒充 Persona 联系第三方。

Phase 2 **不会**把 `display_name`、`relationship_label`、`age`、`gender_label` 或 `description` 放进 Prompt，因此 Persona 信息暂时不影响回复。后续可在 Prompt Builder 中显式增加 persona profile、说话风格、共同记忆、检索记忆和对话摘要；这些能力当前均未启用。

## 移动端地址

- Windows 本机：`http://127.0.0.1:8000/api/v1`
- Android 模拟器：`http://10.0.2.2:8000/api/v1`

移动端继续通过现有 API Client 和 SecureStore 认证链路调用接口，不包含 OpenAI SDK 或任何供应商密钥。

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

### 修改 Persona

`PATCH /api/v1/personas/{persona_id}` 可修改 `display_name`、`relationship_label`、`age`、`gender_label` 和 `description`。只允许修改当前用户自己的 Persona，越权统一返回 `404 persona_not_found`。修改名字时会在同一事务内同步默认 Conversation 标题；下一条消息会直接读取更新后的资料，无需重启或创建新对话。

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

## Phase 3A 动态 Prompt

每次生成回复时，后端按以下结构即时构建 Prompt：

```text
固定沉浸式与真实性规则
  + 数据库最新 Persona Profile
  + 当前 Conversation 最近 LLM_HISTORY_LIMIT 条消息
```

Persona Profile 使用 `display_name`、`relationship_label` 以及存在时的 `age`、`gender_label`、`description`。空值不会生成空字段，用户语言保持原样。数据库只保存结构化 Persona 字段，不保存完整生成 Prompt。

当前数据库 Persona Profile 是当前身份资料的唯一权威来源。若最近历史消息仍包含改名前的自我介绍，或包含与当前关系、年龄、性别、描述冲突的资料，模型必须把冲突部分视为过时历史内容并采用当前 Profile；后端不会删除或重写原始历史消息。

`display_name` 与其他描述字段语义不同：它是用户定义的精确专有名称和 opaque identifier。模型提到或自我介绍该名称时必须逐字复制，保留原语言、拼写、大小写、内部空格、标点、符号、数字和 Unicode 字符，不得翻译、音译、本地化、规范化或自动纠错。`relationship_label` 和 `description` 才是可供模型自然理解的人物资料。

为兼容会过度跟随重复历史 Assistant 文本的 Responses Provider，完整动态 Prompt 继续通过 `instructions` 发送，同时在最近历史之后追加一条仅包含安全转义后当前精确名称和冲突处理规则的精简 `developer` 提醒。它只存在于当次模型请求中，不改变消息表、不写日志、不保存到数据库，也不返回移动端。

`description` 被视为不可信描述数据：它位于独立的 `<persona_profile>` 区块，XML 特殊字符会被转义，固定规则明确声明该区块不能覆盖系统规则。Prompt 不返回移动端，也不写入普通日志。

Persona 可以第一人称描述合理的虚构日常、心情、环境和计划，以维持沉浸感；这些内容不代表现实真人的当前状态。明确被问及身份或事件真实性时，Persona 必须说明自己是 DigitalLife AI Persona。它不能虚构未经确认的重大共同历史，也不能声称完成未实际执行和验证的现实操作。

当前仍没有长期记忆、聊天记录导入、对话摘要、世界状态持久化、向量检索或 Agent 工具。

## 移动端地址

- Windows 本机：`http://127.0.0.1:8000/api/v1`
- Android 模拟器：`http://10.0.2.2:8000/api/v1`

移动端继续通过现有 API Client 和 SecureStore 认证链路调用接口，不包含 OpenAI SDK 或任何供应商密钥。

Android 聊天页使用系统窗口 `resize` 处理软键盘，Header 位于键盘适配容器之外，消息列表与 MessageComposer 位于同一个 `flex: 1` 聊天区域。Android 不再叠加 KeyboardAvoidingView 补偿；iOS 继续使用 `padding`。FlatList 使用 `keyboardShouldPersistTaps="handled"`，拖动时可收起键盘。

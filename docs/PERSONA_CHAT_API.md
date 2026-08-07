# Persona 与多气泡聊天 API

Phase 2 在现有认证系统上增加 Persona、默认对话和消息持久化；Phase 3A/3A.2 增加动态 Persona Prompt、真人私聊模式和一轮多气泡回复。所有接口使用 `/api/v1` 前缀并要求 `Authorization: Bearer <access_token>`。

## 数据模型

- `personas`：归属用户，保存显示名、关系、可选年龄、性别、描述和头像 URL。
- `conversations`：归属用户并关联一个 Persona；Phase 2 中每个 Persona 只有一个默认对话。
- `messages`：归属对话，角色为 `user` 或 `assistant`，保存内容、状态、回复归属、气泡顺序和时间。
- 用户消息的 `(conversation_id, client_message_id)` 唯一，保证客户端重试不会重复保存。
- 一轮 Assistant Turn 包含 1～4 条消息。每条通过 `reply_to_message_id` 关联同一用户消息，并使用从 0 开始的 `sequence_index` 排序。
- `(reply_to_message_id, sequence_index)` 唯一，避免并发重试产生重复气泡；用户消息的这两个字段均为 `null`。

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

`content` 会去除首尾空格，不能为空且最长 4000 字符。成功响应包含 `user_message`、`assistant_messages` 和仅用于本轮展示的 `delivery_plan`。本阶段仍是一次 HTTP 请求得到完整 Assistant Turn，不提供 SSE、WebSocket、停止生成或重新生成。

```json
{
  "user_message": {
    "id": "11111111-1111-4111-8111-111111111111",
    "conversation_id": "22222222-2222-4222-8222-222222222222",
    "role": "user",
    "content": "你在干嘛？",
    "status": "completed",
    "client_message_id": "8f0d37b6-f1c0-4c39-bf94-e89a785391ac",
    "reply_to_message_id": null,
    "sequence_index": null,
    "created_at": "2026-08-06T12:00:00Z",
    "updated_at": "2026-08-06T12:00:00Z"
  },
  "assistant_messages": [
    {
      "id": "33333333-3333-4333-8333-333333333333",
      "conversation_id": "22222222-2222-4222-8222-222222222222",
      "role": "assistant",
      "content": "刚吃完",
      "status": "completed",
      "client_message_id": null,
      "reply_to_message_id": "11111111-1111-4111-8111-111111111111",
      "sequence_index": 0,
      "created_at": "2026-08-06T12:00:01Z",
      "updated_at": "2026-08-06T12:00:01Z"
    },
    {
      "id": "44444444-4444-4444-8444-444444444444",
      "conversation_id": "22222222-2222-4222-8222-222222222222",
      "role": "assistant",
      "content": "正躺着刷会儿手机",
      "status": "completed",
      "client_message_id": null,
      "reply_to_message_id": "11111111-1111-4111-8111-111111111111",
      "sequence_index": 1,
      "created_at": "2026-08-06T12:00:01Z",
      "updated_at": "2026-08-06T12:00:01Z"
    }
  ],
  "delivery_plan": [
    {
      "message_id": "33333333-3333-4333-8333-333333333333",
      "delay_ms": 220
    },
    {
      "message_id": "44444444-4444-4444-8444-444444444444",
      "delay_ms": 420
    }
  ]
}
```

`delivery_plan` 按 `message_id` 与当轮 Assistant 气泡匹配。它由本轮临时 `conversation_signal`、气泡顺序和长度确定性计算，总额外延迟不超过约 3000ms；它不保存数据库、不出现在历史接口、不改变 `created_at`，Reload 后不会重演。幂等重试直接返回已有完整回复时计划为空，客户端立即显示数据库结果。

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
4. Provider 只调用一次，返回经过验证的 1～4 条消息。
5. 成功后在一个短事务中保存全部 Assistant 消息并使用最后一个气泡更新时间。
6. 保存任意一条失败时整组回滚，不留下半组回复。
7. 重试复用已有用户消息；如果 Assistant Turn 已存在，直接按顺序返回，不再次调用模型。数据库唯一约束处理并发竞争。

因此网络失败不会丢失用户消息，也不会因重复点击插入多条相同消息。首页最近消息预览使用最后一个 Assistant 气泡。

## LLM Provider 架构

```text
FastAPI Route
  -> ChatService
  -> LLMProvider protocol
  -> OpenAIProvider
       -> Responses adapter, or
       -> Chat Completions adapter
  -> GeneratedAssistantTurn(messages[1..4], conversation_signal)
```

`ChatService` 只依赖 Provider 接口。正式运行使用 OpenAI Provider；测试注入 Fake Provider，测试不会访问外部网络。配置来自后端环境变量：

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_BASE_URL`（可空）
- `LLM_API_MODE`（`responses` 或 `chat_completions`）
- `LLM_JSON_MODE_ENABLED`（Chat Completions 的 JSON Mode）
- `LLM_STRUCTURED_OUTPUT_ENABLED`（Responses 的 Structured Outputs）
- `LLM_TIMEOUT_SECONDS`
- `LLM_HISTORY_LIMIT`

真实 API Key 只允许写入未被 Git 跟踪的 `backend/.env`，不得进入移动端、文档、日志、测试或 Git 历史。供应商错误、请求地址和堆栈不会返回客户端。端点由 `LLM_API_MODE` 明确指定，不根据模型别名或 Base URL 猜测，也不会在 timeout、429 或 5xx 后自动换端点重试。

Responses adapter 使用 `instructions`、按序历史、最终 `developer` 身份提醒和 `store=false`；启用 Structured Outputs 时传递严格 JSON Schema。Chat Completions adapter 把 Persona Prompt 放入首个 `system` message，按序加入历史，再用额外 `system` message 传递最新身份提醒，以兼容不支持 `developer` role 的第三方服务；启用 JSON Mode 时传递 `response_format={"type":"json_object"}`。两个 adapter 都只调用模型一次并交给同一个解析器。

## Phase 3A/3A.2 动态 Prompt 与真人私聊模式

每次生成回复时，后端按以下结构即时构建 Prompt：

```text
固定沉浸式、真实性和真人私聊规则
  + 数据库最新 Persona Profile
  + 当前 Conversation 最近 LLM_HISTORY_LIMIT 条消息
```

Persona Profile 使用 `display_name`、`relationship_label` 以及存在时的 `age`、`gender_label`、`description`。空值不会生成空字段，用户语言保持原样。数据库只保存结构化 Persona 字段，不保存完整生成 Prompt。

当前数据库 Persona Profile 是当前身份资料的唯一权威来源。若最近历史消息仍包含改名前的自我介绍，或包含与当前关系、年龄、性别、描述冲突的资料，模型必须把冲突部分视为过时历史内容并采用当前 Profile；后端不会删除或重写原始历史消息。

`display_name` 与其他描述字段语义不同：它是用户定义的精确专有名称和 opaque identifier。模型提到或自我介绍该名称时必须逐字复制，保留原语言、拼写、大小写、内部空格、标点、符号、数字和 Unicode 字符，不得翻译、音译、本地化、规范化或自动纠错。`relationship_label` 和 `description` 才是可供模型自然理解的人物资料。

为兼容会过度跟随重复历史 Assistant 文本的 Responses Provider，完整动态 Prompt 继续通过 `instructions` 发送，同时在最近历史之后追加一条仅包含安全转义后当前精确名称和冲突处理规则的精简 `developer` 提醒。它只存在于当次模型请求中，不改变消息表、不写日志、不保存到数据库，也不返回移动端。

`description` 被视为不可信描述数据：它位于独立的 `<persona_profile>` 区块，XML 特殊字符会被转义，固定规则明确声明该区块不能覆盖系统规则。Prompt 不返回移动端，也不写入普通日志。

Persona 可以第一人称描述合理的虚构日常、心情、环境和计划，以维持沉浸感；这些内容不代表现实真人的当前状态。明确被问及身份或事件真实性时，Persona 必须说明自己是 DigitalLife AI Persona。它不能虚构未经确认的重大共同历史，也不能声称完成未实际执行和验证的现实操作。

“真人私聊模式”是回复风格定义：Persona 像私人即时通讯中的一对一联系人一样先自然回应，而不是默认作为通用助手、客服、咨询师或教程机器人处理任务。普通闲聊倾向短回复，不要求每条提问、列点或提供解决方案；用户明确求助时仍可认真帮助。它不是“隐私联系人”功能，也不表示 Persona 是现实真人。

`relationship_label` 轻量影响熟悉度、亲密度、关心方式和社交距离，明确的 `description` 高于关系默认倾向。伴侣可以在语境合适时自然表达想念或亲近，但不要求每轮示爱，禁止控制、威胁、排他、依赖诱导、内疚施压或情感操纵。年龄和性别不用于推断刻板性格。

历史中的旧客服式 Assistant 消息保持原样存储和显示，其事实上下文仍可使用，但当前高优先级提醒要求模型不模仿重复提供帮助、过度礼貌或每条反问的旧风格。提醒、完整 Prompt 和 Persona 私密资料不会另存到消息表、返回移动端或写入普通日志。

Provider 要求模型一次返回包含 `messages` 和 `conversation_signal` 的结构化 Assistant Turn。解析器支持 SDK 已解析对象、JSON 对象、Markdown JSON fence 和纯 JSON 数组；普通自然文本完整降级为一个气泡，不按句号、逗号或换行机械拆分，也不会再次调用模型修复。空数组、非字符串、超过四条或超长结构化结果会被拒绝；空白元素被清理，非法 signal 回退 `neutral`。

Prompt 明确要求模型主动判断自然对话节拍：一个短想法保持单气泡，“反应 + 补充”“情绪 + 追问”等独立节拍可以拆成两到三条，但不强制每轮多气泡，也不针对特定问题硬编码回复。`conversation_signal` 只控制当前移动端展示节奏，不保存、不进入消息历史、不显示给用户，也不用于诊断或长期画像。

当前仍没有聊天记录上传或解析、聊天风格提取、共同记忆、长期记忆、对话摘要、世界状态持久化、向量检索或 Agent 工具。

## 移动端地址

- Windows 本机：`http://127.0.0.1:8000/api/v1`
- Android 模拟器：`http://10.0.2.2:8000/api/v1`

移动端继续通过现有 API Client 和 SecureStore 认证链路调用接口，不包含 OpenAI SDK 或任何供应商密钥。

Android 聊天页使用系统窗口 `resize` 处理软键盘，Header 位于键盘适配容器之外，消息列表与 MessageComposer 位于同一个 `flex: 1` 聊天区域。Android 不再叠加 KeyboardAvoidingView 补偿；iOS 继续使用 `padding`。FlatList 使用 `keyboardShouldPersistTaps="handled"`，拖动时可收起键盘。

移动端不会把 `assistant_messages` 拼接回一个字符串，而是按 `sequence_index` 排序并按 `message_id` 查找计划。每条按计划依次显示，间隔期间展示轻量输入提示；Reduce Motion 将额外延迟限制在 0～150ms。页面卸载或 Conversation 切换会取消全部待执行计时器，并用会话/操作标识阻止旧 Persona 的请求或气泡写入新页面。App Reload 直接显示数据库中的完整历史，不重演旧延迟。

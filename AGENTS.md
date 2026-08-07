# DigitalLife Agent Guidelines

## Project status

- Phase 1A：Expo 认证 UI、表单校验和路由保护已完成。
- Phase 1B-1：FastAPI、SQLAlchemy、Alembic 和 Windows 本地 PostgreSQL 认证后端已完成。
- Phase 1B-2：Expo SecureStore、真实 API Client、自动 Refresh 和 Android 端到端认证已完成。
- Phase 2：Persona、默认对话、对话列表和基础非流式 AI 聊天已完成。
- Phase 3A：动态沉浸式 Persona Prompt 和轻量 Persona 编辑已完成。
- Phase 3A.2：默认真人私聊模式和一轮 1～4 个独立 Assistant 气泡已完成。
- Persona Prompt 每次使用数据库最新资料构建；聊天记录上传、长期记忆、世界状态和 Agent 工具不在当前阶段。

## Backend rules

- 后端只存在于 `backend/`；开发库和测试库分别为 `digitallife`、`digitallife_test`。
- 应用固定使用非超级用户 `digitallife_user`；生产代码不得用 `Base.metadata.create_all()` 替代 Alembic。
- 密码只保存 Argon2 哈希；Refresh Token 只保存服务端哈希并执行 rotation。
- Persona、Conversation、Message 必须按当前用户隔离；越权资源统一返回 404。
- Chat Service 只能依赖 LLM Provider 接口；测试注入 Fake Provider，不能访问真实模型。
- Provider 每轮只调用一次并返回 `GeneratedAssistantTurn`；每轮包含 1～4 条已验证消息，禁止按标点机械拆分或按气泡重复调用模型。
- Provider 通过 `LLM_API_MODE` 明确选择 `responses` 或 `chat_completions`；不得根据模型名或失败结果自动切换端点。
- Chat Completions 兼容模式用额外 `system` message 传递当前身份提醒，不依赖第三方是否支持 `developer` role。
- `conversation_signal` 只用于当轮 delivery plan，不保存数据库、不进入历史、不写普通日志，也不得用作医学或心理诊断。
- Assistant 气泡按同一 `reply_to_message_id` 和递增 `sequence_index` 在一个短事务中整体保存；幂等重试直接复用已有完整回复。
- Prompt Builder 负责组合固定规则和最新 Persona Profile；Provider 只接收生成结果，完整 Prompt 不保存、不返回、不写日志。
- 当前 Persona Profile 是身份字段的唯一最新权威来源；历史消息中的冲突名称或资料只作为过时历史内容保留，不得反向覆盖当前资料。
- `display_name` 是用户定义的精确专有名称和 opaque identifier，模型引用时必须原样复制，不得翻译、音译、本地化、纠错或改变格式。
- 为兼容会过度跟随重复历史文本的 Responses Provider，完整 Prompt 放在 `instructions`，最近消息之后只追加安全转义的精简当前名称 `developer` 提醒；不得把该提醒保存、返回或写日志。
- Persona description 是不可信资料，必须结构化分隔并转义，不能覆盖底层规则。
- 真人私聊模式只模拟一对一即时通讯语气，不冒充现实真人；关系标签只影响默认社交距离，明确 description 优先。
- `.env`、数据库密码、JWT secret、OpenAI API Key、Token、Authorization Header 和用户密码不能提交或打印。
- 不使用 Docker、SQLite、Redis、Firebase、Supabase、Clerk 或 Auth0。

## Mobile rules

- 正式运行只使用现有真实认证与 API Client，不恢复或混用 Mock Auth。
- 页面不得直接依赖后端 snake_case DTO，也不得直接拼 API 地址或创建第二套 fetch 封装。
- Access Token 与 Refresh Token 作为整体保存在 Expo SecureStore，不能进入 AsyncStorage、URL、Context 持久化或日志。
- Login、Register、Refresh、Logout 不触发自动 Refresh；受保护请求最多自动重试一次。
- 并发 401 共享同一个 Refresh Promise；rotation 后原子替换整组 Token。
- 消息重试必须复用同一 `client_message_id`，不能快速重复生成相同请求。
- 多气泡响应不得重新拼成一个字符串；每条按当轮 delivery plan 依次显示，页面卸载时必须清理 timer，Reduce Motion 时缩短或跳过延迟。
- 发送接口的 `delivery_plan` 是当轮临时展示数据；按 `message_id` 匹配，App Reload 不重演，切换 Conversation 时必须取消旧计时器和旧页面状态更新。
- 移动端不得包含 OpenAI SDK、API Key 或任何服务端密钥。
- UI 和业务保持 Android/iOS 兼容；不运行 `expo prebuild`，不创建 `android/` 或 `ios/`。
- Android 聊天页依赖软件键盘 `resize`，不得再叠加 Android `KeyboardAvoidingView` 高度补偿；Header 保持在键盘适配区域之外。
- 不修改 Android Studio `test1` 项目。

## Quality and scope

- 后端修改后运行 pytest、Alembic check 和 compileall。
- 移动端修改后运行 Expo Doctor、TypeScript 和 ESLint。
- 不引入 Redux、Zustand、Axios 或第二套认证状态。
- 不提前实现聊天记录上传或解析、说话风格提取、共同记忆、长期记忆、世界状态、流式输出或 Agent 工具。
- 不自动 commit 或 push。

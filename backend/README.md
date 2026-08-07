# DigitalLife Backend

FastAPI + PostgreSQL 后端。Phase 1B 提供真实认证；Phase 2 增加 Persona、消息和可替换 LLM Provider；Phase 3A 增加动态沉浸式 Persona Prompt；Phase 3A.2 增加默认真人私聊模式和一轮 1～4 个独立消息气泡。后端独立运行，不嵌入手机 App。

## 本机环境

- Python 3.11
- PostgreSQL 17（Windows 服务 `postgresql-x64-17`）
- 开发库 `digitallife`
- 测试库 `digitallife_test`
- 应用角色 `digitallife_user`（非超级用户）

## 首次安装

```powershell
Set-Location 'C:\Users\wzc\Desktop\DigitalLife-App\backend'
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

在 `.env` 中填写本机数据库密码和至少 32 字符的随机 JWT secret。需要真实 AI 回复时，再手动填写 `OPENAI_API_KEY` 和 `OPENAI_MODEL`；不要提交或输出 `.env`。

Phase 2 LLM 配置：

```dotenv
OPENAI_API_KEY=replace-me
OPENAI_MODEL=replace-me
OPENAI_BASE_URL=
LLM_API_MODE=responses
LLM_JSON_MODE_ENABLED=true
LLM_STRUCTURED_OUTPUT_ENABLED=true
LLM_TIMEOUT_SECONDS=30
LLM_HISTORY_LIMIT=20
```

## Migration

```powershell
$env:Path = "C:\Program Files\PostgreSQL\17\bin;$env:Path"
.\.venv\Scripts\Activate.ps1
alembic upgrade head
alembic current
alembic check
```

应用启动时不会执行 `Base.metadata.create_all()`；表结构只通过 Alembic 管理。

## 启动 API

```powershell
Set-Location 'C:\Users\wzc\Desktop\DigitalLife-App\backend'
.\scripts\start-dev.ps1
```

地址：

- Health：`http://127.0.0.1:8000/health`
- Swagger：`http://127.0.0.1:8000/docs`
- OpenAPI：`http://127.0.0.1:8000/openapi.json`

## 测试

```powershell
Set-Location 'C:\Users\wzc\Desktop\DigitalLife-App\backend'
.\scripts\run-tests.ps1
```

测试脚本强制设置 `APP_ENV=test`，应用会使用 `TEST_DATABASE_URL`。测试启动时还会检查数据库名必须是 `digitallife_test`。

## 安全边界

- 密码使用 pwdlib Argon2 哈希。
- Access Token 是固定 HS256 算法的短期 JWT。
- Refresh Token 是高熵随机字符串，数据库只保存 HMAC-SHA256 哈希。
- Refresh 使用行锁和单事务 rotation；旧 Token 立即吊销。
- 数据库操作使用 `digitallife_user`，不使用 `postgres` 超级用户。
- 请求密码、Authorization Header 和完整 Token 不写入日志。
- OpenAI API Key 只存在于后端 `.env`；移动端、日志和错误响应均不包含供应商密钥。
- LLM 调用失败返回统一 `ai_service_unavailable`，不泄露供应商原始异常。
- Provider 日志只记录 API 模式、操作、模型、HTTP 状态、错误类型/代码和重试属性等脱敏元数据；不记录 Prompt、正文、Header、Key、Token 或供应商完整错误 Body。

## Persona 与聊天

- 创建 Persona 和默认对话在一个事务中完成。
- 所有资源查询按当前用户隔离；越权访问统一返回 404。
- 用户消息使用 `client_message_id` 幂等保存，重试不会复制消息。
- LLM 网络调用不长时间占用数据库事务；一次用户消息只调用一次模型。
- Provider 返回经过验证的 `GeneratedAssistantTurn`，包含 1～4 条非空消息；兼容服务未返回合法 JSON 时可将完整原始文本安全降级为一个气泡，不按标点机械拆分。
- `LLM_API_MODE=responses` 使用 Responses adapter；`LLM_API_MODE=chat_completions` 使用 Chat Completions adapter。端点由配置决定，不根据模型名推断，也不会在失败后自动切换或再次产生收费请求。
- Responses Structured Outputs 和 Chat JSON Mode 分别由独立开关控制；关闭参数后 Prompt 仍要求严格 JSON，并由统一解析器校验。
- 每条 Assistant 消息使用同一 `reply_to_message_id` 和从 0 开始的 `sequence_index` 独立保存；整组气泡在同一个短事务中成功或全部回滚。
- 同次输出的 `conversation_signal` 只计算本轮临时 `delivery_plan`；两者均不写数据库、不进入历史或 Prompt。FastAPI 不 sleep，逐条展示由移动端负责。
- 已有完整 Assistant Turn 的幂等重试直接返回数据库消息，不再次请求模型。
- `ChatService` 依赖 Provider 接口，自动化测试注入 Fake Provider，不请求真实模型。
- Prompt Builder 每次组合固定底层规则、数据库最新 Persona Profile 和当前对话最近消息。
- `description` 作为不可信描述数据放入独立 XML-like 区块并转义，不能覆盖固定规则。
- Provider 显式接收动态 `system_prompt`，不再硬编码统一 Prompt。
- 真人私聊模式要求普通闲聊优先短而自然的联系人反应，避免默认客服套话；明确求助时仍正常提供帮助。
- `relationship_label` 只轻量影响亲密度和社交距离，明确 `description` 优先；伴侣关系允许语境合适的亲近表达，但不强制每轮示爱，也禁止控制、威胁和情感操纵。
- 旧 Assistant 消息保留事实上下文和原始显示，但不作为当前客服式语气的权威风格样例。
- Prompt 不写数据库、不返回移动端、不进入普通日志。
- Persona 可描述虚构日常，但不能冒充现实真人状态、虚构重大共同历史或声称完成未验证工具操作。
- 当前仍没有聊天记录上传或解析、说话风格提取、共同记忆、长期记忆、世界状态、流式输出或 Agent 工具。
- 旧微信机器人仅用于参考显式分段、队列去抖和长度相关节奏思想；没有迁移 wxauto、微信发送、旧聊天、旧记忆或旧密钥。

完整契约见 [`docs/AUTH_API.md`](../docs/AUTH_API.md)。
Persona 与聊天契约见 [`docs/PERSONA_CHAT_API.md`](../docs/PERSONA_CHAT_API.md)。

## 与移动端联合运行

先确认 PostgreSQL 服务，再运行 `scripts/start-dev.ps1`，最后从 `mobile/` 启动 Expo。Windows 本机使用 `127.0.0.1:8000`；Android Emulator 通过 `10.0.2.2:8000` 访问同一 FastAPI 进程。

移动端 Token 存储与 Refresh 行为见 [`docs/MOBILE_AUTH.md`](../docs/MOBILE_AUTH.md)。网络 logout 失败时移动端仍会清除本机会话，但服务端 Refresh Token 可能继续有效到过期或后续吊销。

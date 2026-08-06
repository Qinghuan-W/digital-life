# DigitalLife Backend

FastAPI + PostgreSQL 后端。Phase 1B 提供真实认证；Phase 2 增加 Persona、消息和可替换 LLM Provider；Phase 3A 增加动态沉浸式 Persona Prompt。后端独立运行，不嵌入手机 App。

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

## Persona 与聊天

- 创建 Persona 和默认对话在一个事务中完成。
- 所有资源查询按当前用户隔离；越权访问统一返回 404。
- 用户消息使用 `client_message_id` 幂等保存，重试不会复制消息。
- LLM 网络调用不长时间占用数据库事务；成功后再保存 Assistant 回复。
- `ChatService` 依赖 Provider 接口，自动化测试注入 Fake Provider，不请求真实模型。
- Prompt Builder 每次组合固定底层规则、数据库最新 Persona Profile 和当前对话最近消息。
- `description` 作为不可信描述数据放入独立 XML-like 区块并转义，不能覆盖固定规则。
- Provider 显式接收动态 `system_prompt`，不再硬编码统一 Prompt。
- Prompt 不写数据库、不返回移动端、不进入普通日志。
- Persona 可描述虚构日常，但不能冒充现实真人状态、虚构重大共同历史或声称完成未验证工具操作。
- 当前仍没有长期记忆、聊天记录导入、世界状态、流式输出或 Agent 工具。

完整契约见 [`docs/AUTH_API.md`](../docs/AUTH_API.md)。
Persona 与聊天契约见 [`docs/PERSONA_CHAT_API.md`](../docs/PERSONA_CHAT_API.md)。

## 与移动端联合运行

先确认 PostgreSQL 服务，再运行 `scripts/start-dev.ps1`，最后从 `mobile/` 启动 Expo。Windows 本机使用 `127.0.0.1:8000`；Android Emulator 通过 `10.0.2.2:8000` 访问同一 FastAPI 进程。

移动端 Token 存储与 Refresh 行为见 [`docs/MOBILE_AUTH.md`](../docs/MOBILE_AUTH.md)。网络 logout 失败时移动端仍会清除本机会话，但服务端 Refresh Token 可能继续有效到过期或后续吊销。

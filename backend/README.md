# DigitalLife Backend

Phase 1B-1 FastAPI + PostgreSQL 真实认证后端。它独立运行，不嵌入手机 App；移动端当前仍使用 Mock Auth。

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

在 `.env` 中填写本机数据库密码和至少 32 字符的随机 JWT secret。不要提交 `.env`。当前开发机已由初始化脚本生成真实 `.env`。

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

完整契约见 [`docs/AUTH_API.md`](../docs/AUTH_API.md)。

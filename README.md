# DigitalLife

DigitalLife 是规划中的跨平台 AI 陪伴与生活 Agent。目前已完成两个阶段：

- **Phase 1A**：Expo/React Native 移动端认证 UI、路由保护和内存 Mock Auth。
- **Phase 1B-1**：Windows 本地 PostgreSQL + FastAPI 真实认证后端。

移动端仍保留 Mock Auth，尚未连接真实 API。AI 聊天、Persona、记忆和 Agent 功能均未开发。

## 架构

```text
未来 Android Emulator
  -> http://10.0.2.2:8000
  -> FastAPI Routes
  -> Auth Service
  -> Repositories / SQLAlchemy
  -> Windows PostgreSQL 17 (localhost:5432)
```

## 目录

```text
DigitalLife-App/
├── mobile/                 # Phase 1A Expo App，仍使用 Mock Auth
├── backend/                # Phase 1B-1 FastAPI 后端
│   ├── app/
│   ├── alembic/
│   ├── tests/
│   └── scripts/
├── docs/AUTH_API.md        # 认证 API 契约
├── AGENTS.md
└── README.md
```

## 后端运行

当前 Windows 开发机使用本地 PostgreSQL 服务、`digitallife` 开发库、`digitallife_test` 测试库和非超级用户 `digitallife_user`。

```powershell
Set-Location 'C:\Users\wzc\Desktop\DigitalLife-App\backend'
.\scripts\start-dev.ps1
```

- Swagger：`http://127.0.0.1:8000/docs`
- Health：`http://127.0.0.1:8000/health`

运行测试：

```powershell
Set-Location 'C:\Users\wzc\Desktop\DigitalLife-App\backend'
.\scripts\run-tests.ps1
```

Migration：

```powershell
Set-Location 'C:\Users\wzc\Desktop\DigitalLife-App\backend'
$env:Path = "C:\Program Files\PostgreSQL\17\bin;$env:Path"
.\.venv\Scripts\Activate.ps1
alembic upgrade head
alembic current
alembic check
```

本地秘密只存放于被 Git 忽略的 `backend/.env`；仓库只提交 `.env.example`。

## 移动端运行

```powershell
Set-Location 'C:\Users\wzc\Desktop\DigitalLife-App\mobile'
npm run android
```

Android Emulator 中的 `10.0.2.2` 映射 Windows 主机，因此下一阶段连接 API 时使用 `http://10.0.2.2:8000/api/v1`，不是 `localhost`。

## 下一阶段

Phase 1B-2 将使用 Expo SecureStore、移动端 API Client、自动 Refresh 和真实 Auth Context 替换当前 Mock 流程，并在 Android 上完成端到端真实注册登录。本阶段不包含这些改动。

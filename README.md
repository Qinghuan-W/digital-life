# DigitalLife

DigitalLife 是规划中的跨平台 AI 陪伴与生活 Agent。当前认证基础设施已完成三个阶段：

- **Phase 1A**：Expo/React Native 认证页面、表单校验和路由保护。
- **Phase 1B-1**：Windows 本地 PostgreSQL 17 + FastAPI 真实认证后端。
- **Phase 1B-2**：Expo SecureStore、真实 API Client、自动 Refresh 和 Android 端到端认证。

AI 聊天、Persona、记忆和 Agent 功能尚未开发。

## 当前架构

```text
React Native UI
  -> Auth Context + reducer
  -> Auth Service
  -> API Client / Expo SecureStore
  -> http://10.0.2.2:8000/api/v1
  -> FastAPI / SQLAlchemy
  -> Windows PostgreSQL 17
```

Android Emulator 中 `10.0.2.2` 映射 Windows 主机；模拟器里的 `localhost` 指模拟器自己。

## 本地启动顺序

1. 确认 Windows 服务 `postgresql-x64-17` 正在运行。
2. 启动 FastAPI：

```powershell
Set-Location 'C:\Users\wzc\Desktop\DigitalLife-App\backend'
.\scripts\start-dev.ps1
```

3. 启动 Android AVD `Medium_Phone_API_36.0`。
4. 启动 Expo：

```powershell
Set-Location 'C:\Users\wzc\Desktop\DigitalLife-App\mobile'
npx expo start --offline --android
```

本机 Swagger 为 `http://127.0.0.1:8000/docs`，健康检查为 `http://127.0.0.1:8000/health`。

## 配置与验证

- `backend/.env` 保存本机数据库凭据和 JWT secret。
- `mobile/.env` 只包含公开 API 地址 `EXPO_PUBLIC_API_URL`。
- 两个真实 `.env` 均被 Git 忽略；仓库只保留 `.env.example`。

```powershell
Set-Location 'C:\Users\wzc\Desktop\DigitalLife-App\mobile'
npx expo-doctor
npx tsc --noEmit
npm run lint

Set-Location 'C:\Users\wzc\Desktop\DigitalLife-App\backend'
.\scripts\run-tests.ps1
```

认证契约见 [docs/AUTH_API.md](docs/AUTH_API.md)，移动端实现说明见 [docs/MOBILE_AUTH.md](docs/MOBILE_AUTH.md)。

## 下一阶段

Phase 2 只规划基础 AI 聊天能力；本阶段没有实现 AI、Persona、记忆、日历或 Agent 工具。

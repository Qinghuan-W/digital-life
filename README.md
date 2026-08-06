# DigitalLife

DigitalLife 是规划中的跨平台 AI 陪伴与生活 Agent。当前已完成认证基础设施和第一版基础聊天：

- **Phase 1A**：Expo/React Native 认证页面、表单校验和路由保护。
- **Phase 1B-1**：Windows 本地 PostgreSQL 17 + FastAPI 真实认证后端。
- **Phase 1B-2**：Expo SecureStore、真实 API Client、自动 Refresh 和 Android 端到端认证。
- **Phase 2**：Persona 创建、默认对话、首页对话列表、消息持久化和基础非流式 AI 聊天。
- **Phase 3A**：根据最新 Persona 资料动态构建沉浸式 Prompt，并支持轻量资料编辑。

Persona 的姓名、关系、年龄、性别和描述现在会影响下一条 AI 回复。数据库中的当前 Persona Profile 高于历史消息中的冲突身份资料；历史消息不会因改名而被重写。`display_name` 是必须原样使用的精确名称，不允许模型翻译、本地化或改变格式。Prompt 不保存到数据库；长期记忆、聊天记录上传、世界状态、流式输出和 Agent 工具尚未开发。

## 当前架构

```text
React Native UI
  -> Auth Context / Persona & Conversation services
  -> API Client / Expo SecureStore
  -> http://10.0.2.2:8000/api/v1
  -> FastAPI Routes / Services / Repositories
  -> Dynamic Prompt Builder (base rules + latest Persona profile + recent messages)
  -> LLM Provider (OpenAI Responses API)
  -> SQLAlchemy
  -> Windows PostgreSQL 17
```

Android Emulator 中 `10.0.2.2` 映射 Windows 主机；模拟器里的 `localhost` 指模拟器自己。
Android 聊天页使用 `softwareKeyboardLayoutMode: "resize"`，Header 位于键盘适配区域之外，消息列表与输入框共享可伸缩聊天区域；iOS 单独使用 `KeyboardAvoidingView` 的 `padding` 行为。

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

- `backend/.env` 保存本机数据库凭据、JWT secret 及本地 LLM 配置。`OPENAI_API_KEY` 和 `OPENAI_MODEL` 必须由开发者手动填写。
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

认证契约见 [docs/AUTH_API.md](docs/AUTH_API.md)，Persona/聊天契约见 [docs/PERSONA_CHAT_API.md](docs/PERSONA_CHAT_API.md)，移动端认证实现见 [docs/MOBILE_AUTH.md](docs/MOBILE_AUTH.md)。

## 当前限制

- Persona 可生成沉浸式虚构日常，但不代表现实真人的当前状态。
- 未确认的重大共同历史不能作为真实记忆生成。
- 暂无聊天记录上传、共同记忆、长期记忆或世界状态持久化。
- 暂无流式输出和头像上传。
- 暂无可执行现实操作的 Agent 工具。
- 当前仍运行在 Windows 本地开发环境。

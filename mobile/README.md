# DigitalLife Mobile

Expo SDK 57 + React Native + TypeScript + Expo Router 移动端。Phase 1B-2 已接入真实认证；Phase 2 已接入 Persona、对话列表和基础非流式聊天。

## 认证实现

- `src/features/auth/auth-context.tsx`：唯一认证状态，负责初始化、提交状态、用户和错误。
- `src/features/auth/auth-service.ts`：注册、登录、恢复、资料更新与退出。
- `src/services/api-client.ts`：fetch、超时、统一错误、Bearer Header、单次重试和并发 Refresh 锁。
- `src/services/token-storage.ts`：使用 `digitallife.auth.tokens` SecureStore key 原子保存 Token 组。
- `src/services/api-mappers.ts`：将后端 snake_case DTO 转换为 App camelCase 类型。

用户对象不会持久化；每次启动都使用保存的 Token 调用 `/auth/me` 获取最新资料。Mock Auth 文件已移除，正式代码中没有 Mock import。

## Persona 与聊天

- 首页从真实 `/conversations` 加载对话并支持下拉刷新。
- 创建 Persona 使用底部弹窗；成功后直接进入自动创建的默认对话。
- Persona 和 Conversation 服务复用现有 `api-client.ts`，DTO 通过 mapper 转成 camelCase。
- 聊天消息先乐观显示；失败时保留消息和重试按钮，并复用同一个客户端 UUID。
- 移动端没有 OpenAI SDK、API Key 或第二套 fetch 封装。

## 环境变量

复制 `.env.example` 为 `.env`：

```dotenv
EXPO_PUBLIC_API_URL=http://10.0.2.2:8000/api/v1
```

`EXPO_PUBLIC_` 只能保存公开 API 地址，不能放 JWT secret、数据库密码或 Token。新增或修改 `.env` 后必须重启 Metro。

## 运行与检查

```powershell
Set-Location 'C:\Users\wzc\Desktop\DigitalLife-App\mobile'
npm install
npx expo start --offline --android
npx expo-doctor
npx tsc --noEmit
npm run lint
```

先启动 PostgreSQL 与 FastAPI，再启动 AVD `Medium_Phone_API_36.0` 和 Expo。Android Emulator 使用 `10.0.2.2` 访问 Windows，不能使用 `localhost`。

认证安全与恢复流程见 [../docs/MOBILE_AUTH.md](../docs/MOBILE_AUTH.md)，Persona/聊天 API 见 [../docs/PERSONA_CHAT_API.md](../docs/PERSONA_CHAT_API.md)。当前 Persona 信息尚未进入 Prompt，也没有流式输出、聊天记录上传或长期记忆。

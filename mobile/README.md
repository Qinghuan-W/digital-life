# DigitalLife Mobile

Expo SDK 57 + React Native + TypeScript + Expo Router 移动端。Phase 1B-2 已将 Phase 1A Mock Auth 替换为 FastAPI/PostgreSQL 真实认证。

## 认证实现

- `src/features/auth/auth-context.tsx`：唯一认证状态，负责初始化、提交状态、用户和错误。
- `src/features/auth/auth-service.ts`：注册、登录、恢复、资料更新与退出。
- `src/services/api-client.ts`：fetch、超时、统一错误、Bearer Header、单次重试和并发 Refresh 锁。
- `src/services/token-storage.ts`：使用 `digitallife.auth.tokens` SecureStore key 原子保存 Token 组。
- `src/services/api-mappers.ts`：将后端 snake_case DTO 转换为 App camelCase 类型。

用户对象不会持久化；每次启动都使用保存的 Token 调用 `/auth/me` 获取最新资料。Mock Auth 文件已移除，正式代码中没有 Mock import。

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

完整安全与恢复流程见 [../docs/MOBILE_AUTH.md](../docs/MOBILE_AUTH.md)。下一阶段是基础 AI 聊天，本阶段未实现 AI 功能。

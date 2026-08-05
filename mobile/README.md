# DigitalLife Mobile

Expo SDK 57 + React Native + TypeScript + Expo Router 移动端。Phase 1A 认证 UI 已完成，认证与资料数据目前仍只存在内存中。Phase 1B-1 FastAPI/PostgreSQL 后端已在相邻 `backend/` 目录完成，但本阶段没有连接手机端。

## 页面与路由

- `/`：首次欢迎入口；已完成欢迎后转到登录
- `/(auth)/login`、`/(auth)/register`：公开认证页面
- `/(app)`、`/(app)/profile`：需临时登录状态的页面

根布局负责路由保护；退出后不能通过 Android 返回键重新进入受保护页面。

## 命令

```powershell
npm install
npm run android
npm run ios
npm run web
npx expo-doctor
npx tsc --noEmit
npm run lint
```

## Mock 边界

`src/features/auth/mock-auth-service.ts` 提供约 650ms 延迟的登录、注册和资料更新。它不访问网络、不保存账号或 Token。Phase 1B 应在此边界接入 FastAPI/PostgreSQL 真实认证，并使用 Expo SecureStore 持久化 Token。

下一阶段 Phase 1B-2 才会新增 API Client 和 Expo SecureStore，并把 Android 开发 Base URL 设置为 `http://10.0.2.2:8000/api/v1`。`10.0.2.2` 是 Android Emulator 访问 Windows 主机的专用地址。

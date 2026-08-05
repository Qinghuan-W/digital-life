# DigitalLife Mobile

Expo SDK 57 + React Native + TypeScript + Expo Router 移动端。当前为 Phase 1A 认证 UI 骨架，认证与资料数据只存在内存中。

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

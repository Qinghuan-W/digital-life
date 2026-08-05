# DigitalLife

DigitalLife 是一个规划中的跨平台 AI 陪伴与生活 Agent 应用。当前完成 **Phase 1A：移动端认证 UI 与前端流程骨架**；账号、会话和资料均为内存 Mock，不连接后端、不保存真实 Token，也不会持久化。

## 当前状态

- Expo SDK 57、React Native 0.86、Expo Router、TypeScript strict
- 欢迎页、登录页、注册页、登录后首页、个人资料页
- 表单校验、密码显示/隐藏、提交加载态、错误态和键盘适配
- Context + reducer 管理临时认证状态，根路由守卫保护 `(app)` 页面
- Mock 登录、Mock 注册、显示名称更新和退出登录
- 已在 Windows 11 的 Android API 36 模拟器与 Expo Go 中实际验证
- 未创建后端、数据库、真实账号、聊天、Persona、记忆或日历功能

## 目录

```text
mobile/src/
├── app/
│   ├── index.tsx
│   ├── (auth)/              # 登录与注册
│   └── (app)/               # 受保护首页与个人资料
├── components/ui/           # 输入框、按钮、页面容器、品牌与错误提示
├── constants/theme.ts       # 颜色、间距、圆角与字号
└── features/auth/           # Mock 服务、状态、类型与校验
```

## 运行 Android

先启动 Android 模拟器，再执行：

```powershell
Set-Location 'C:\Users\wzc\Desktop\DigitalLife-App\mobile'
npm install
npm run android
```

网络受限时可使用 `npx expo start --offline --android`。若 Expo Go 连接主机地址失败，Android Emulator 可尝试 `exp://10.0.2.2:8081`。

## 质量检查

```powershell
npx expo-doctor
npx tsc --noEmit
npm run lint
```

## 下一阶段

Phase 1B 建议接入 FastAPI、PostgreSQL 和真实认证 API，并用 Expo SecureStore 保存真实 Token。届时应替换 `mobile/src/features/auth/mock-auth-service.ts`，保留现有页面、校验和路由边界；在真实接口完成前，不应把当前 Mock 描述为已注册或已持久化的账号。

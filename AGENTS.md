# DigitalLife Agent Guidelines

## Project goal

DigitalLife 的最终目标是兼容 Android 与 iOS 的 AI 陪伴与生活 Agent。移动端使用 React Native、Expo、Expo Router 和 TypeScript；后端计划使用 FastAPI 与 PostgreSQL。

## Current scope

- Phase 1A 已完成移动端欢迎、登录、注册、登录后首页、个人资料和前端路由保护。
- 当前认证仅为内存 Mock：不连接后端、不创建真实账号、不保存 Token、重启后不保留会话。
- 下一阶段 Phase 1B 才接入 FastAPI、PostgreSQL、真实认证 API 与 SecureStore。
- 不提前实现 AI 聊天、Persona、聊天记录导入、共同记忆、长期记忆、日历、提醒或待办 Agent。

## Engineering rules

- UI 与核心业务必须同时兼容 Android 和 iOS，不把业务逻辑写死为 Android 专用实现。
- 优先使用 Expo 与 React Native 跨平台能力；没有明确必要性时不创建原生工程，不运行 `expo prebuild`。
- 不擅自加入 Redux、NativeBase、React Native Paper 等大型依赖。
- 保持 TypeScript strict、Expo Router 路由清晰；修改后运行 Expo Doctor、TypeScript 和 lint。
- 不提交 API Key、访问令牌、`.env`、聊天记录或私人数据。
- Mock 与真实实现必须明确区分；真实认证接入时从 `features/auth/mock-auth-service.ts` 边界替换。
- 每次只完成用户指定阶段，不提前开发后续功能。
- 不修改用户的 Android Studio `test1` 测试项目。

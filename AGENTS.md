# DigitalLife Agent Guidelines

## Project status

- Phase 1A 已完成 Expo 认证 UI、表单校验和路由保护。
- Phase 1B-1 已完成 FastAPI、SQLAlchemy、Alembic 和 Windows 本地 PostgreSQL 认证后端。
- Phase 1B-2 已完成 Expo SecureStore、真实 API Client、自动 Refresh 和 Android 端到端认证。
- 下一阶段是基础 AI 聊天；不得提前加入 Persona、长期记忆、日历或 Agent 工具。

## Backend rules

- 后端只存在于 `backend/`；开发库与测试库分别为 `digitallife`、`digitallife_test`。
- 应用角色固定为非超级用户 `digitallife_user`；生产代码不得用 `Base.metadata.create_all()` 代替 Alembic。
- 密码只保存 Argon2 哈希；Refresh Token 只保存服务端哈希并执行 rotation。
- `.env`、数据库密码、JWT secret、Token、Authorization Header 和用户密码不能提交或打印。
- 不使用 Docker、SQLite、Redis、Firebase、Supabase、Clerk 或 Auth0。

## Mobile rules

- 正式运行只使用 `auth-service.ts`，不得恢复或混用 Mock Auth。
- 页面不得直接依赖后端 snake_case DTO，也不得直接拼 API 地址。
- Access Token 与 Refresh Token 只能作为一个整体保存在 Expo SecureStore，不能放入 AsyncStorage、URL、Context 持久化或日志。
- Login、Register、Refresh、Logout 不触发自动 Refresh；受保护请求最多自动重试一次。
- 并发 401 必须共享同一个 Refresh Promise，rotation 后原子替换整组 Token。
- UI 与业务保持 Android/iOS 兼容；不运行 `expo prebuild`，不创建 `android/` 或 `ios/`。
- 不修改 Android Studio `test1` 项目。

## Quality and scope

- 后端修改后运行 pytest、Alembic check 和 compileall。
- 移动端修改后运行 Expo Doctor、TypeScript 和 ESLint。
- 不引入 Redux、Zustand 或第二套认证状态。
- 每次只完成用户指定阶段，不自动 commit 或 push。

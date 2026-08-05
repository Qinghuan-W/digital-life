# DigitalLife Agent Guidelines

## Project status

- Phase 1A 已完成 Expo 移动端认证 UI、路由保护和内存 Mock Auth。
- Phase 1B-1 已完成 FastAPI、SQLAlchemy、Alembic 和 Windows 本地 PostgreSQL 真实认证后端。
- 手机端尚未连接后端；Phase 1B-2 才使用 SecureStore 和 API Client 替换 Mock Auth。

## Backend rules

- 后端只存在于 `backend/`，不能写入手机 App。
- 开发和测试分别使用 `digitallife`、`digitallife_test`，应用角色固定为非超级用户 `digitallife_user`。
- 生产代码不得用 `Base.metadata.create_all()` 代替 Alembic。
- 密码只保存 Argon2 哈希；Refresh Token 只保存服务端哈希。
- `.env`、数据库密码、JWT secret 和 Token 不能提交、打印或写入文档。
- 测试必须确认使用 `digitallife_test`，不能污染开发库。
- 不使用 Docker、SQLite、Redis、Celery、Firebase、Supabase、Clerk 或 Auth0。

## Mobile rules

- 当前继续保留 Mock Auth，不调用 FastAPI，不安装 SecureStore。
- UI 与核心业务必须兼容 Android/iOS；不运行 `expo prebuild`，不创建原生 `android/` 或 `ios/`。
- 不修改 Android Studio `test1` 项目。

## Scope rules

- 不提前开发 AI 聊天、Persona、记忆、日历、Agent、文件上传或管理员后台。
- 新增依赖前确认必要性；保持结构清晰，不创建无意义抽象。
- 后端修改后运行 pytest、Alembic check 和 compileall；移动端修改后运行 Expo Doctor、TypeScript 和 lint。
- 每次只完成用户指定阶段，不自动 commit 或 push。

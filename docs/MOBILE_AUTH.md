# DigitalLife Mobile Authentication

## 架构

```text
React Native UI
  -> Auth Context + reducer
  -> Auth Service
  -> API Client
  -> Expo SecureStore
  -> FastAPI
  -> PostgreSQL
```

页面只使用 camelCase `User` 与认证方法，不直接读取 snake_case DTO、Token 或 API 地址。`api-mappers.ts` 是 DTO 与业务类型的唯一转换层。

## Android API 地址

Android Emulator 的 `localhost` 指模拟器自身；`10.0.2.2` 才映射 Windows 主机。因此：

- Android：`http://10.0.2.2:8000/api/v1`
- Windows 本机：`http://127.0.0.1:8000/api/v1`

API 地址由 `EXPO_PUBLIC_API_URL` 集中读取。修改 `mobile/.env` 后必须重启 Metro。

## SecureStore

唯一 key 为 `digitallife.auth.tokens`，保存一个 JSON 对象：

```json
{
  "accessToken": "<access-token>",
  "refreshToken": "<refresh-token>",
  "tokenType": "bearer",
  "expiresIn": 900
}
```

两枚 Token 通过一次 `setItemAsync` 原子替换。Logout 使用 `deleteItemAsync` 清除。JSON 无法解析或结构不合法时，存储层会执行最佳努力清除并按未登录处理。密码和完整用户对象从不持久化。

## 启动 Session 恢复

1. Auth Context 以 `initializing` 启动，根布局只显示 LoadingScreen。
2. 从 SecureStore 读取 Token；没有 Token 时进入 `unauthenticated`。
3. 有 Token 时请求 `/auth/me` 获取最新用户。
4. Access Token 失效时 API Client 自动 Refresh 并重试 `/auth/me`。
5. 成功进入 `authenticated`；失败清理失效 Token 并进入登录流程。

初始化完成前路由不跳转，因此不会闪现欢迎页、登录页或受保护首页。

## 401 自动 Refresh 与并发锁

受保护请求第一次返回 401 后：

1. 读取当前 Refresh Token。
2. 所有并发 401 共享同一个 `refreshPromise`，只发出一次 `/auth/refresh`。
3. 保存 rotation 返回的新 Token 组。
4. 使用新 Access Token 重试原请求一次。

如果另一请求已完成 Refresh，当前请求直接使用存储中的新 Access Token，不再重复 rotation。重试仍为 401、Refresh 失败或 Token 缺失时，客户端清除 SecureStore、通知 Auth Context 会话失效并回到登录页。锁在 `finally` 中释放，不存在无限 Refresh 循环。

Login、Register、Refresh 和 Logout 均不参与自动 Refresh。

## Logout

正常退出会将当前 Refresh Token 发送到 `/auth/logout`，收到 204 后清除 SecureStore、清空 Context，并用 `replace` 进入登录页。Android 返回键不能重新进入受保护路由。

如果服务器不可用，客户端仍会尝试清除本机 SecureStore 并退出，避免用户卡在登录态；此时服务器端 Refresh Token 可能继续有效到自然过期或后续吊销，这是离线 logout 的已知安全边界。

## 错误与加载状态

- 后端业务错误、网络错误和请求超时使用不同错误类型。
- 页面只显示面向用户的信息，不显示堆栈、SQL、密码或 Token。
- Login/Register 新提交会清理旧错误并阻止重复提交。
- 资料保存失败不做乐观更新，原用户保持不变。
- 所有请求路径都会结束 loading 状态。

## Token 安全边界

- Token 只进入 SecureStore 和内存请求 Header，不进入 AsyncStorage、URL、日志或 Git。
- `EXPO_PUBLIC_` 中只有公开 API 地址，没有服务端密钥。
- App 不保存密码；后端只保存 Argon2 哈希。
- Refresh Token 数据库中只保存 HMAC-SHA256 哈希。
- Expo Go 适用于当前本地开发验证；正式发布仍需按发布流程审查设备安全策略。

## 本地启动顺序

```powershell
# 1. 确认 postgresql-x64-17 正在运行

# 2. FastAPI
Set-Location 'C:\Users\wzc\Desktop\DigitalLife-App\backend'
.\scripts\start-dev.ps1

# 3. 启动 AVD Medium_Phone_API_36.0

# 4. Expo
Set-Location 'C:\Users\wzc\Desktop\DigitalLife-App\mobile'
npx expo start --offline --android
```

## 当前限制与下一阶段

- 当前只有邮箱密码认证和显示名称修改，没有邮箱验证、忘记密码或第三方登录。
- 开发环境是 Windows 本地 FastAPI/PostgreSQL，尚未部署云端。
- 下一阶段为 Phase 2 基础 AI 聊天；本阶段不包含 Persona、长期记忆、日历或 Agent。

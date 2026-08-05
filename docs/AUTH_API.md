# DigitalLife Authentication API

Phase 1B-1 提供独立 FastAPI 认证后端；Phase 1B-2 移动端已经通过 API Client 和 Expo SecureStore 接入这些接口。

## Base URL

- Windows 本机：`http://127.0.0.1:8000/api/v1`
- Android Emulator：`http://10.0.2.2:8000/api/v1`

Android Emulator 中的 `127.0.0.1` 指模拟器自身，`10.0.2.2` 才映射到 Windows 主机。

## 错误格式

```json
{
  "error": "error_code",
  "message": "面向用户的错误信息"
}
```

可能的业务代码包括 `validation_error`、`email_already_registered`、`invalid_credentials`、`invalid_access_token`、`invalid_refresh_token`、`refresh_token_expired`、`refresh_token_revoked`、`user_inactive`、`database_unavailable` 和 `internal_error`。

## Health

`GET /health` 不使用 `/api/v1` 前缀。

成功 `200`：

```json
{"status":"ok","database":"ok"}
```

## Register

`POST /api/v1/auth/register`，成功 `201`，重复邮箱 `409`。

```json
{
  "email": "user@example.com",
  "display_name": "Wang",
  "password": "replace-with-user-input"
}
```

成功响应同时包含 `user`、15 分钟 Access Token、30 天 Refresh Token、`token_type: bearer` 和 `expires_in: 900`。邮箱会 trim 并转小写，显示名称会 trim。

## Login

`POST /api/v1/auth/login`，成功 `200`。

```json
{
  "email": "user@example.com",
  "password": "replace-with-user-input"
}
```

邮箱不存在和密码错误均返回 `401 invalid_credentials`，不会暴露邮箱是否存在。

## Current user

`GET /api/v1/auth/me`，成功 `200`。

```http
Authorization: Bearer <access-token>
```

Access Token 是 HS256 JWT，包含 `sub`、`type=access`、`iat`、`exp` 和 `jti`。错误类型、过期、伪造或缺少必要字段的 Token 均被拒绝。

## Update profile

`PATCH /api/v1/users/me`，成功 `200`。本阶段只能修改当前用户的显示名称。

```json
{"display_name":"New Name"}
```

## Refresh

`POST /api/v1/auth/refresh`，成功 `200`。

```json
{"refresh_token":"<opaque-refresh-token>"}
```

每次刷新都会 rotation：旧 Token 立即吊销，新 Token 返回客户端，数据库记录 `replaced_by_token_id`。数据库只保存基于服务端密钥的 HMAC-SHA256 哈希，不保存可直接使用的明文 Refresh Token。

## Logout

`POST /api/v1/auth/logout`，成功 `204`。

```json
{"refresh_token":"<opaque-refresh-token>"}
```

Logout 吊销对应 Refresh Token；该 Token 后续刷新会返回 `refresh_token_revoked`。

## 移动端接入状态

移动端使用 `http://10.0.2.2:8000/api/v1`、Expo SecureStore 和原生 fetch。受保护请求遇到 401 时共享单例 Refresh Promise，成功后原子替换 Access/Refresh Token 并只重试原请求一次。Login、Register、Refresh 和 Logout 不触发自动 Refresh；Refresh 失败会清除本机会话并回到登录页。详见 [MOBILE_AUTH.md](MOBILE_AUTH.md)。

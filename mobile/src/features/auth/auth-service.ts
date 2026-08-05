import { apiRequest } from '@/services/api-client';
import { mapApiUser, mapAuthResponse } from '@/services/api-mappers';
import { clearTokens, getTokens, saveTokens } from '@/services/token-storage';
import { AuthResponseDto, ApiUser } from '@/types/api';
import { AuthResult, AuthSession, LoginCredentials, RegisterCredentials } from '@/types/auth';
import { User } from '@/types/user';

export async function register(credentials: RegisterCredentials): Promise<AuthResult> {
  const dto = await apiRequest<AuthResponseDto>('/auth/register', {
    method: 'POST',
    body: {
      email: credentials.email.trim().toLowerCase(),
      display_name: credentials.displayName.trim(),
      password: credentials.password,
    },
  });
  const result = mapAuthResponse(dto);
  await saveTokens(result.session);
  return result;
}

export async function login(credentials: LoginCredentials): Promise<AuthResult> {
  const dto = await apiRequest<AuthResponseDto>('/auth/login', {
    method: 'POST',
    body: {
      email: credentials.email.trim().toLowerCase(),
      password: credentials.password,
    },
  });
  const result = mapAuthResponse(dto);
  await saveTokens(result.session);
  return result;
}

export async function getCurrentUser(): Promise<User> {
  const dto = await apiRequest<ApiUser>('/auth/me', { authenticated: true });
  return mapApiUser(dto);
}

export async function restoreSession(): Promise<User | null> {
  const tokens = await getTokens();
  if (!tokens) {
    return null;
  }
  return getCurrentUser();
}

export async function updateProfile(displayName: string): Promise<User> {
  const dto = await apiRequest<ApiUser>('/users/me', {
    method: 'PATCH',
    authenticated: true,
    body: { display_name: displayName.trim() },
  });
  return mapApiUser(dto);
}

export async function logout(): Promise<string | null> {
  let tokens: AuthSession | null = null;
  let warning: string | null = null;

  try {
    tokens = await getTokens();
  } catch {
    warning = '已退出当前会话，但无法读取本机 Token 完成服务器吊销。';
  }

  if (tokens) {
    try {
      await apiRequest<void>('/auth/logout', {
        method: 'POST',
        body: { refresh_token: tokens.refreshToken },
      });
    } catch {
      warning = '已退出本机账号，但服务器暂时无法确认 Token 吊销。';
    }
  }

  try {
    await clearTokens();
  } catch {
    warning = '已退出当前会话，但安全存储清理失败，请重启 App 后重试。';
  }
  return warning;
}

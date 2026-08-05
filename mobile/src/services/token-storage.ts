import * as SecureStore from 'expo-secure-store';

import { AuthSession } from '@/types/auth';

export const AUTH_TOKENS_KEY = 'digitallife.auth.tokens';

export class TokenStorageError extends Error {
  constructor(message = '无法安全保存登录状态，请重试。') {
    super(message);
    this.name = 'TokenStorageError';
  }
}

function isAuthSession(value: unknown): value is AuthSession {
  if (!value || typeof value !== 'object') {
    return false;
  }

  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.accessToken === 'string' &&
    candidate.accessToken.length > 0 &&
    typeof candidate.refreshToken === 'string' &&
    candidate.refreshToken.length > 0 &&
    candidate.tokenType === 'bearer' &&
    typeof candidate.expiresIn === 'number' &&
    Number.isFinite(candidate.expiresIn) &&
    candidate.expiresIn > 0
  );
}

export async function getTokens(): Promise<AuthSession | null> {
  let serialized: string | null;

  try {
    serialized = await SecureStore.getItemAsync(AUTH_TOKENS_KEY);
  } catch {
    throw new TokenStorageError('无法读取安全登录状态，请重新登录。');
  }

  if (!serialized) {
    return null;
  }

  try {
    const parsed: unknown = JSON.parse(serialized);
    if (isAuthSession(parsed)) {
      return parsed;
    }
  } catch {
    // Corrupted values are cleared below and treated as signed out.
  }

  try {
    await SecureStore.deleteItemAsync(AUTH_TOKENS_KEY);
  } catch {
    // The unusable value is never returned, even if best-effort cleanup fails.
  }
  return null;
}

export async function saveTokens(tokens: AuthSession): Promise<void> {
  try {
    await SecureStore.setItemAsync(AUTH_TOKENS_KEY, JSON.stringify(tokens));
  } catch {
    throw new TokenStorageError();
  }
}

export async function clearTokens(): Promise<void> {
  try {
    await SecureStore.deleteItemAsync(AUTH_TOKENS_KEY);
  } catch {
    throw new TokenStorageError('无法清除本机登录状态，请重试。');
  }
}

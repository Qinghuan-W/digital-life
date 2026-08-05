import { mapTokenResponse } from './api-mappers';
import {
  ApiError,
  NetworkError,
  RequestTimeoutError,
  SessionExpiredError,
} from './api-errors';
import { clearTokens, getTokens, saveTokens } from './token-storage';

import { ApiErrorResponse, RefreshResponseDto } from '@/types/api';
import { AuthSession } from '@/types/auth';

const DEFAULT_TIMEOUT_MS = 12_000;
const configuredBaseUrl = process.env.EXPO_PUBLIC_API_URL?.trim().replace(/\/+$/, '');

type HttpMethod = 'GET' | 'POST' | 'PATCH';

type RequestOptions = {
  method?: HttpMethod;
  body?: unknown;
  authenticated?: boolean;
  timeoutMs?: number;
};

type SessionExpiredHandler = () => void;

let refreshPromise: Promise<AuthSession> | null = null;
let sessionExpiredHandler: SessionExpiredHandler | null = null;

export function setSessionExpiredHandler(handler: SessionExpiredHandler | null): void {
  sessionExpiredHandler = handler;
}

function getApiBaseUrl(): string {
  if (!configuredBaseUrl) {
    throw new NetworkError('缺少 EXPO_PUBLIC_API_URL，无法连接认证服务。');
  }
  return configuredBaseUrl;
}

function isApiErrorResponse(value: unknown): value is ApiErrorResponse {
  if (!value || typeof value !== 'object') {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return typeof candidate.error === 'string' && typeof candidate.message === 'string';
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get('content-type') ?? '';
  const isJson = contentType.toLowerCase().includes('application/json');
  let payload: unknown;

  if (isJson) {
    try {
      payload = await response.json();
    } catch {
      payload = undefined;
    }
  }

  if (!response.ok) {
    if (isApiErrorResponse(payload)) {
      throw new ApiError(payload.error, payload.message, response.status);
    }
    throw new ApiError(
      response.status >= 500 ? 'server_error' : 'request_failed',
      response.status >= 500 ? '服务器暂时无法处理请求。' : '请求未成功。',
      response.status,
    );
  }

  if (!isJson || payload === undefined) {
    throw new ApiError('invalid_response', '服务器返回了无法识别的响应。', response.status);
  }

  return payload as T;
}

async function execute<T>(
  path: string,
  options: RequestOptions,
  accessToken?: string,
): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), options.timeoutMs ?? DEFAULT_TIMEOUT_MS);
  const headers: Record<string, string> = { Accept: 'application/json' };

  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  try {
    const response = await fetch(`${getApiBaseUrl()}${path}`, {
      method: options.method ?? 'GET',
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: controller.signal,
    });
    return await parseResponse<T>(response);
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    if (error instanceof Error && error.name === 'AbortError') {
      throw new RequestTimeoutError();
    }
    throw new NetworkError();
  } finally {
    clearTimeout(timeout);
  }
}

async function expireSession(): Promise<never> {
  try {
    await clearTokens();
  } catch {
    // The app must still leave authenticated state if secure cleanup fails.
  }
  sessionExpiredHandler?.();
  throw new SessionExpiredError();
}

async function performRefresh(): Promise<AuthSession> {
  const currentTokens = await getTokens();
  if (!currentTokens) {
    return expireSession();
  }

  try {
    const dto = await execute<RefreshResponseDto>('/auth/refresh', {
      method: 'POST',
      body: { refresh_token: currentTokens.refreshToken },
      authenticated: false,
    });
    const nextTokens = mapTokenResponse(dto);
    await saveTokens(nextTokens);
    return nextTokens;
  } catch {
    return expireSession();
  }
}

async function refreshTokens(): Promise<AuthSession> {
  if (!refreshPromise) {
    refreshPromise = performRefresh().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  if (!options.authenticated) {
    return execute<T>(path, options);
  }

  const initialTokens = await getTokens();
  if (!initialTokens) {
    return expireSession();
  }

  try {
    return await execute<T>(path, options, initialTokens.accessToken);
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 401) {
      throw error;
    }
  }

  const latestTokens = await getTokens();
  const retryTokens =
    latestTokens && latestTokens.accessToken !== initialTokens.accessToken
      ? latestTokens
      : await refreshTokens();

  try {
    return await execute<T>(path, options, retryTokens.accessToken);
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return expireSession();
    }
    throw error;
  }
}

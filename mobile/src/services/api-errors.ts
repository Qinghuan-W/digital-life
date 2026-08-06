export class ApiError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class NetworkError extends Error {
  constructor(message = '无法连接服务器，请确认 FastAPI 已启动并检查网络。') {
    super(message);
    this.name = 'NetworkError';
  }
}

export class RequestTimeoutError extends Error {
  constructor(message = '请求超时，请稍后重试。') {
    super(message);
    this.name = 'RequestTimeoutError';
  }
}

export class SessionExpiredError extends Error {
  constructor(message = '登录状态已失效，请重新登录。') {
    super(message);
    this.name = 'SessionExpiredError';
  }
}

export function getUserFacingError(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.code) {
      case 'email_already_registered':
        return '该邮箱已经注册，请直接登录。';
      case 'invalid_credentials':
        return '邮箱或密码错误。';
      case 'database_unavailable':
        return '服务暂时不可用，请稍后重试。';
      case 'validation_error':
        return '提交内容不符合要求，请检查后重试。';
      case 'user_inactive':
        return '该账号当前不可用。';
      case 'ai_service_unavailable':
        return 'AI 服务暂时不可用，请稍后重试。';
      case 'conversation_not_found':
        return '该对话不存在或已被删除。';
      default:
        return error.status >= 500 ? '服务器暂时无法处理请求，请稍后重试。' : error.message;
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return '操作未完成，请稍后重试。';
}

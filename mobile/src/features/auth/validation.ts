import { LoginCredentials, RegisterCredentials } from './auth-types';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export type LoginFieldErrors = Partial<Record<keyof LoginCredentials, string>>;

export type RegisterFormValues = RegisterCredentials & {
  confirmPassword: string;
};

export type RegisterFieldErrors = Partial<Record<keyof RegisterFormValues, string>>;

export function validateEmail(email: string): string | undefined {
  const normalizedEmail = email.trim();

  if (!normalizedEmail) {
    return '请输入邮箱地址';
  }

  if (!EMAIL_PATTERN.test(normalizedEmail)) {
    return '请输入有效的邮箱地址';
  }

  return undefined;
}

export function validatePassword(password: string): string | undefined {
  if (!password) {
    return '请输入密码';
  }

  if (password.length < 8) {
    return '密码至少需要 8 位';
  }

  if (password.length > 128) {
    return '密码不能超过 128 位';
  }

  return undefined;
}

export function validateLoginForm(values: LoginCredentials): LoginFieldErrors {
  const errors: LoginFieldErrors = {};
  const emailError = validateEmail(values.email);
  const passwordError = validatePassword(values.password);

  if (emailError) {
    errors.email = emailError;
  }

  if (passwordError) {
    errors.password = passwordError;
  }

  return errors;
}

export function validateRegisterForm(values: RegisterFormValues): RegisterFieldErrors {
  const errors: RegisterFieldErrors = {};
  const trimmedName = values.displayName.trim();
  const emailError = validateEmail(values.email);
  const passwordError = validatePassword(values.password);

  if (!trimmedName) {
    errors.displayName = '请输入显示名称';
  } else if (trimmedName.length < 2) {
    errors.displayName = '显示名称至少需要 2 个字符';
  }

  if (emailError) {
    errors.email = emailError;
  }

  if (passwordError) {
    errors.password = passwordError;
  }

  if (!values.confirmPassword) {
    errors.confirmPassword = '请再次输入密码';
  } else if (values.confirmPassword !== values.password) {
    errors.confirmPassword = '两次输入的密码不一致';
  }

  return errors;
}

export function validateDisplayName(displayName: string): string | undefined {
  const trimmedName = displayName.trim();

  if (!trimmedName) {
    return '显示名称不能为空';
  }

  if (trimmedName.length < 2) {
    return '显示名称至少需要 2 个字符';
  }

  return undefined;
}

export function hasValidationErrors<T extends object>(errors: T): boolean {
  return Object.keys(errors).length > 0;
}

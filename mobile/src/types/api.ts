export type ApiUser = {
  id: string;
  email: string;
  display_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type RegisterRequest = {
  email: string;
  display_name: string;
  password: string;
};

export type LoginRequest = {
  email: string;
  password: string;
};

export type AuthResponseDto = RefreshResponseDto & {
  user: ApiUser;
};

export type RefreshResponseDto = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
};

export type ApiErrorResponse = {
  error: string;
  message: string;
};

import { User } from './user';

export type AuthStatus = 'initializing' | 'unauthenticated' | 'authenticated';

export type LoginCredentials = {
  email: string;
  password: string;
};

export type RegisterCredentials = {
  displayName: string;
  email: string;
  password: string;
};

export type AuthSession = {
  accessToken: string;
  refreshToken: string;
  tokenType: 'bearer';
  expiresIn: number;
};

export type AuthResult = {
  user: User;
  session: AuthSession;
};

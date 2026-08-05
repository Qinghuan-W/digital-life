export type AuthStatus = 'loading' | 'unauthenticated' | 'authenticated';

export type AuthUser = {
  id: string;
  displayName: string;
  email: string;
};

export type LoginCredentials = {
  email: string;
  password: string;
};

export type RegisterCredentials = {
  displayName: string;
  email: string;
  password: string;
};

export type AuthState = {
  status: AuthStatus;
  user: AuthUser | null;
  hasSeenWelcome: boolean;
};

export type AuthContextValue = AuthState & {
  completeWelcome: () => void;
  returnToWelcome: () => void;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  updateProfile: (displayName: string) => Promise<void>;
  logout: () => void;
};

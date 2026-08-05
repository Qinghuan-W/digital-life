import { LoginCredentials, RegisterCredentials, AuthStatus } from '@/types/auth';
import { User } from '@/types/user';

export type { LoginCredentials, RegisterCredentials } from '@/types/auth';

export type AuthUser = User;

export type AuthState = {
  status: AuthStatus;
  user: User | null;
  hasSeenWelcome: boolean;
  error: string | null;
  isSubmitting: boolean;
};

export type AuthContextValue = AuthState & {
  completeWelcome: () => void;
  returnToWelcome: () => void;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  restoreSession: () => Promise<void>;
  updateProfile: (displayName: string) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
};

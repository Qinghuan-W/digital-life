import {
  createContext,
  PropsWithChildren,
  useCallback,
  useContext,
  useMemo,
  useReducer,
} from 'react';

import {
  AuthContextValue,
  AuthState,
  AuthUser,
  LoginCredentials,
  RegisterCredentials,
} from './auth-types';
import { mockLogin, mockRegister, mockUpdateProfile } from './mock-auth-service';

type AuthAction =
  | { type: 'COMPLETE_WELCOME' }
  | { type: 'RETURN_TO_WELCOME' }
  | { type: 'AUTH_REQUESTED' }
  | { type: 'AUTHENTICATED'; user: AuthUser }
  | { type: 'PROFILE_UPDATED'; user: AuthUser }
  | { type: 'LOGGED_OUT' };

const initialState: AuthState = {
  status: 'unauthenticated',
  user: null,
  hasSeenWelcome: false,
};

const AuthContext = createContext<AuthContextValue | null>(null);

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'COMPLETE_WELCOME':
      return { ...state, hasSeenWelcome: true };
    case 'RETURN_TO_WELCOME':
      return { ...state, hasSeenWelcome: false };
    case 'AUTH_REQUESTED':
      return { ...state, status: 'loading' };
    case 'AUTHENTICATED':
      return {
        status: 'authenticated',
        user: action.user,
        hasSeenWelcome: true,
      };
    case 'PROFILE_UPDATED':
      return { ...state, user: action.user };
    case 'LOGGED_OUT':
      return {
        status: 'unauthenticated',
        user: null,
        hasSeenWelcome: true,
      };
  }
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  const completeWelcome = useCallback(() => {
    dispatch({ type: 'COMPLETE_WELCOME' });
  }, []);

  const returnToWelcome = useCallback(() => {
    dispatch({ type: 'RETURN_TO_WELCOME' });
  }, []);

  const login = useCallback(async (credentials: LoginCredentials) => {
    dispatch({ type: 'AUTH_REQUESTED' });
    const user = await mockLogin(credentials);
    dispatch({ type: 'AUTHENTICATED', user });
  }, []);

  const register = useCallback(async (credentials: RegisterCredentials) => {
    dispatch({ type: 'AUTH_REQUESTED' });
    const user = await mockRegister(credentials);
    dispatch({ type: 'AUTHENTICATED', user });
  }, []);

  const updateProfile = useCallback(
    async (displayName: string) => {
      if (!state.user) {
        return;
      }

      const user = await mockUpdateProfile(state.user, displayName);
      dispatch({ type: 'PROFILE_UPDATED', user });
    },
    [state.user],
  );

  const logout = useCallback(() => {
    dispatch({ type: 'LOGGED_OUT' });
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      completeWelcome,
      returnToWelcome,
      login,
      register,
      updateProfile,
      logout,
    }),
    [completeWelcome, login, logout, register, returnToWelcome, state, updateProfile],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider.');
  }

  return context;
}

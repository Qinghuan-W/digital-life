import {
  createContext,
  PropsWithChildren,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useReducer,
  useRef,
} from 'react';

import * as authService from './auth-service';
import {
  AuthContextValue,
  AuthState,
  AuthUser,
  LoginCredentials,
  RegisterCredentials,
} from './auth-types';

import { setSessionExpiredHandler } from '@/services/api-client';
import { getUserFacingError } from '@/services/api-errors';

type AuthAction =
  | { type: 'COMPLETE_WELCOME' }
  | { type: 'RETURN_TO_WELCOME' }
  | { type: 'RESTORE_STARTED' }
  | { type: 'RESTORED'; user: AuthUser | null }
  | { type: 'RESTORE_FAILED'; error: string }
  | { type: 'OPERATION_STARTED' }
  | { type: 'OPERATION_FAILED'; error: string }
  | { type: 'AUTHENTICATED'; user: AuthUser }
  | { type: 'PROFILE_UPDATED'; user: AuthUser }
  | { type: 'LOGGED_OUT'; warning: string | null }
  | { type: 'SESSION_EXPIRED' }
  | { type: 'CLEAR_ERROR' };

const initialState: AuthState = {
  status: 'initializing',
  user: null,
  hasSeenWelcome: false,
  error: null,
  isSubmitting: false,
};

const AuthContext = createContext<AuthContextValue | null>(null);

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'COMPLETE_WELCOME':
      return { ...state, hasSeenWelcome: true };
    case 'RETURN_TO_WELCOME':
      return { ...state, hasSeenWelcome: false, error: null };
    case 'RESTORE_STARTED':
      return { ...state, status: 'initializing', error: null, isSubmitting: false };
    case 'RESTORED':
      return action.user
        ? {
            status: 'authenticated',
            user: action.user,
            hasSeenWelcome: true,
            error: null,
            isSubmitting: false,
          }
        : {
            ...state,
            status: 'unauthenticated',
            user: null,
            isSubmitting: false,
          };
    case 'RESTORE_FAILED':
      return {
        ...state,
        status: 'unauthenticated',
        user: null,
        error: action.error,
        isSubmitting: false,
      };
    case 'OPERATION_STARTED':
      return { ...state, error: null, isSubmitting: true };
    case 'OPERATION_FAILED':
      return { ...state, error: action.error, isSubmitting: false };
    case 'AUTHENTICATED':
      return {
        status: 'authenticated',
        user: action.user,
        hasSeenWelcome: true,
        error: null,
        isSubmitting: false,
      };
    case 'PROFILE_UPDATED':
      return { ...state, user: action.user, error: null, isSubmitting: false };
    case 'LOGGED_OUT':
      return {
        status: 'unauthenticated',
        user: null,
        hasSeenWelcome: true,
        error: action.warning,
        isSubmitting: false,
      };
    case 'SESSION_EXPIRED':
      return {
        status: 'unauthenticated',
        user: null,
        hasSeenWelcome: true,
        error: '登录状态已失效，请重新登录。',
        isSubmitting: false,
      };
    case 'CLEAR_ERROR':
      return { ...state, error: null };
  }
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [state, dispatch] = useReducer(authReducer, initialState);
  const mountedRef = useRef(false);

  const completeWelcome = useCallback(() => {
    dispatch({ type: 'COMPLETE_WELCOME' });
  }, []);

  const returnToWelcome = useCallback(() => {
    dispatch({ type: 'RETURN_TO_WELCOME' });
  }, []);

  const clearError = useCallback(() => {
    dispatch({ type: 'CLEAR_ERROR' });
  }, []);

  const restoreSession = useCallback(async () => {
    dispatch({ type: 'RESTORE_STARTED' });
    try {
      const user = await authService.restoreSession();
      if (mountedRef.current) {
        dispatch({ type: 'RESTORED', user });
      }
    } catch (error) {
      if (mountedRef.current) {
        dispatch({ type: 'RESTORE_FAILED', error: getUserFacingError(error) });
      }
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    setSessionExpiredHandler(() => {
      if (mountedRef.current) {
        dispatch({ type: 'SESSION_EXPIRED' });
      }
    });
    void restoreSession();

    return () => {
      mountedRef.current = false;
      setSessionExpiredHandler(null);
    };
  }, [restoreSession]);

  const login = useCallback(async (credentials: LoginCredentials) => {
    dispatch({ type: 'OPERATION_STARTED' });
    try {
      const result = await authService.login(credentials);
      if (mountedRef.current) {
        dispatch({ type: 'AUTHENTICATED', user: result.user });
      }
    } catch (error) {
      if (mountedRef.current) {
        dispatch({ type: 'OPERATION_FAILED', error: getUserFacingError(error) });
      }
      throw error;
    }
  }, []);

  const register = useCallback(async (credentials: RegisterCredentials) => {
    dispatch({ type: 'OPERATION_STARTED' });
    try {
      const result = await authService.register(credentials);
      if (mountedRef.current) {
        dispatch({ type: 'AUTHENTICATED', user: result.user });
      }
    } catch (error) {
      if (mountedRef.current) {
        dispatch({ type: 'OPERATION_FAILED', error: getUserFacingError(error) });
      }
      throw error;
    }
  }, []);

  const updateProfile = useCallback(async (displayName: string) => {
    dispatch({ type: 'OPERATION_STARTED' });
    try {
      const user = await authService.updateProfile(displayName);
      if (mountedRef.current) {
        dispatch({ type: 'PROFILE_UPDATED', user });
      }
    } catch (error) {
      if (mountedRef.current) {
        dispatch({ type: 'OPERATION_FAILED', error: getUserFacingError(error) });
      }
      throw error;
    }
  }, []);

  const logout = useCallback(async () => {
    dispatch({ type: 'OPERATION_STARTED' });
    let warning: string | null;
    try {
      warning = await authService.logout();
    } catch {
      warning = '已退出当前会话，但本机安全状态可能需要重启 App 后再次清理。';
    }
    if (mountedRef.current) {
      dispatch({ type: 'LOGGED_OUT', warning });
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      completeWelcome,
      returnToWelcome,
      login,
      register,
      restoreSession,
      updateProfile,
      logout,
      clearError,
    }),
    [
      clearError,
      completeWelcome,
      login,
      logout,
      register,
      restoreSession,
      returnToWelcome,
      state,
      updateProfile,
    ],
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

import { AuthUser, LoginCredentials, RegisterCredentials } from './auth-types';

const MOCK_DELAY_MS = 650;

const FIXED_MOCK_USER: AuthUser = {
  id: 'mock-user-phase-1a',
  displayName: 'DigitalLife User',
  email: 'user@example.com',
};

function waitForMockRequest(): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, MOCK_DELAY_MS);
  });
}

// TODO Phase 1B: Replace this mock service with the real FastAPI Auth API.
export async function mockLogin(_credentials: LoginCredentials): Promise<AuthUser> {
  await waitForMockRequest();
  return { ...FIXED_MOCK_USER };
}

// TODO Phase 1B: Replace this mock service with the real FastAPI Auth API.
export async function mockRegister(credentials: RegisterCredentials): Promise<AuthUser> {
  await waitForMockRequest();

  return {
    id: 'mock-registered-user-phase-1a',
    displayName: credentials.displayName.trim(),
    email: credentials.email.trim().toLowerCase(),
  };
}

// TODO Phase 1B: Persist this change through the real profile API.
export async function mockUpdateProfile(user: AuthUser, displayName: string): Promise<AuthUser> {
  await waitForMockRequest();

  return {
    ...user,
    displayName: displayName.trim(),
  };
}

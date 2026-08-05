import { Stack, useRouter, useSegments } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { LoadingScreen } from '@/components/ui/LoadingScreen';
import { colors } from '@/constants/theme';
import { AuthProvider, useAuth } from '@/features/auth/auth-context';

function RootNavigator() {
  const { status } = useAuth();
  const router = useRouter();
  const segments = useSegments();
  const firstSegment = segments[0];

  useEffect(() => {
    if (status === 'initializing') {
      return;
    }

    const inProtectedApp = firstSegment === '(app)';

    if (status === 'authenticated' && !inProtectedApp) {
      router.replace('/(app)');
    } else if (status === 'unauthenticated' && inProtectedApp) {
      router.replace('/(auth)/login');
    }
  }, [firstSegment, router, status]);

  if (status === 'initializing') {
    return <LoadingScreen message="正在恢复登录状态" />;
  }

  return (
    <>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          animation: 'fade',
          contentStyle: { backgroundColor: colors.background },
          headerShown: false,
        }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="(auth)" />
        <Stack.Screen name="(app)" />
      </Stack>
    </>
  );
}

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <RootNavigator />
      </AuthProvider>
    </SafeAreaProvider>
  );
}

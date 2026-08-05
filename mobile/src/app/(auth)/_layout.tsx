import { Stack } from 'expo-router';

import { colors } from '@/constants/theme';

export default function AuthLayout() {
  return (
    <Stack
      screenOptions={{
        animation: 'slide_from_right',
        contentStyle: { backgroundColor: colors.background },
        headerShown: false,
      }}
    />
  );
}

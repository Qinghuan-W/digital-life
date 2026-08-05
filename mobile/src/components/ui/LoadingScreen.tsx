import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { colors, spacing, typography } from '@/constants/theme';

import { BrandMark } from './BrandMark';
import { PageContainer } from './PageContainer';

type LoadingScreenProps = {
  message?: string;
};

export function LoadingScreen({ message = '正在准备 DigitalLife' }: LoadingScreenProps) {
  return (
    <PageContainer contentStyle={styles.page}>
      <View accessibilityLiveRegion="polite" style={styles.content}>
        <BrandMark size={52} />
        <ActivityIndicator color={colors.brand} size="small" />
        <Text style={styles.message}>{message}</Text>
      </View>
    </PageContainer>
  );
}

const styles = StyleSheet.create({
  page: {
    justifyContent: 'center',
  },
  content: {
    alignItems: 'center',
    gap: spacing.x4,
  },
  message: {
    color: colors.textSecondary,
    fontSize: typography.helper,
  },
});

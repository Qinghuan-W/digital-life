import { StyleSheet, Text, View } from 'react-native';

import { colors, radii, spacing, typography } from '@/constants/theme';

type FormErrorProps = {
  message?: string;
};

export function FormError({ message }: FormErrorProps) {
  if (!message) {
    return null;
  }

  return (
    <View accessibilityLiveRegion="polite" style={styles.container}>
      <Text style={styles.symbol}>!</Text>
      <Text style={styles.message}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'flex-start',
    backgroundColor: colors.errorSoft,
    borderRadius: radii.small,
    flexDirection: 'row',
    gap: spacing.x2,
    paddingHorizontal: spacing.x3,
    paddingVertical: spacing.x3,
  },
  symbol: {
    color: colors.error,
    fontSize: typography.helper,
    fontWeight: '800',
  },
  message: {
    color: colors.error,
    flex: 1,
    fontSize: typography.helper,
    lineHeight: 20,
  },
});

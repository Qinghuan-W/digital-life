import { StyleSheet, Text, View } from 'react-native';

import { colors, radii, spacing, typography } from '@/constants/theme';

export function TypingIndicator() {
  return (
    <View accessibilityLabel="对方正在输入" style={styles.row}>
      <View style={styles.bubble}>
        <Text style={styles.dots}>•••</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', justifyContent: 'flex-start', marginVertical: spacing.x1 },
  bubble: {
    backgroundColor: colors.surface,
    borderBottomLeftRadius: 5,
    borderColor: colors.border,
    borderRadius: radii.card,
    borderWidth: 1,
    paddingHorizontal: spacing.x4,
    paddingVertical: spacing.x2,
  },
  dots: {
    color: colors.textSecondary,
    fontSize: typography.body,
    letterSpacing: 2,
  },
});

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { colors, layout, spacing, typography } from '@/constants/theme';

import { BrandMark } from './BrandMark';

type AuthHeaderProps = {
  title: string;
  subtitle: string;
  onBack?: () => void;
};

export function AuthHeader({ title, subtitle, onBack }: AuthHeaderProps) {
  return (
    <View style={styles.container}>
      <View style={styles.topRow}>
        {onBack ? (
          <Pressable
            accessibilityLabel="返回"
            accessibilityRole="button"
            hitSlop={6}
            onPress={onBack}
            style={({ pressed }) => [styles.backButton, pressed && styles.pressed]}>
            <Text allowFontScaling={false} style={styles.backIcon}>
              ←
            </Text>
          </Pressable>
        ) : (
          <View style={styles.backButton} />
        )}
        <BrandMark size={44} />
      </View>
      <View style={styles.copy}>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.subtitle}>{subtitle}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.x6,
  },
  topRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  backButton: {
    alignItems: 'center',
    height: layout.minimumTouchTarget,
    justifyContent: 'center',
    width: layout.minimumTouchTarget,
  },
  backIcon: {
    color: colors.text,
    fontSize: 25,
    fontWeight: '500',
  },
  pressed: {
    opacity: 0.5,
  },
  copy: {
    gap: spacing.x2,
  },
  title: {
    color: colors.text,
    fontSize: typography.pageTitle,
    fontWeight: '700',
    letterSpacing: -0.5,
    lineHeight: 34,
  },
  subtitle: {
    color: colors.textSecondary,
    fontSize: typography.body,
    lineHeight: 23,
  },
});

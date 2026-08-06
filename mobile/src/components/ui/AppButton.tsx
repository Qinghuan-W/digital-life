import { ActivityIndicator, Pressable, StyleSheet, Text } from 'react-native';

import { colors, layout, radii, spacing, typography } from '@/constants/theme';

type AppButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';

type AppButtonProps = {
  title: string;
  onPress: () => void;
  loading?: boolean;
  disabled?: boolean;
  variant?: AppButtonVariant;
  fullWidth?: boolean;
  accessibilityLabel?: string;
  loadingTitle?: string;
};

export function AppButton({
  title,
  onPress,
  loading = false,
  disabled = false,
  variant = 'primary',
  fullWidth = true,
  accessibilityLabel,
  loadingTitle = '请稍候',
}: AppButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <Pressable
      accessibilityLabel={accessibilityLabel ?? title}
      accessibilityRole="button"
      accessibilityState={{ busy: loading, disabled: isDisabled }}
      disabled={isDisabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.base,
        styles[variant],
        fullWidth && styles.fullWidth,
        pressed && !isDisabled && styles.pressed,
        isDisabled && styles.disabled,
      ]}>
      {loading ? (
        <ActivityIndicator
          accessibilityLabel="正在处理"
          color={variant === 'primary' ? colors.white : colors.brand}
          size="small"
        />
      ) : null}
      <Text style={[styles.label, styles[`${variant}Label`]]}>
        {loading ? loadingTitle : title}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    alignItems: 'center',
    borderRadius: radii.button,
    flexDirection: 'row',
    gap: spacing.x2,
    justifyContent: 'center',
    minHeight: layout.controlHeight,
    paddingHorizontal: spacing.x5,
  },
  fullWidth: {
    alignSelf: 'stretch',
  },
  primary: {
    backgroundColor: colors.brand,
  },
  secondary: {
    backgroundColor: colors.brandSoft,
    borderColor: colors.border,
    borderWidth: 1,
  },
  danger: {
    backgroundColor: colors.errorSoft,
    borderColor: '#E9CACA',
    borderWidth: 1,
  },
  ghost: {
    backgroundColor: 'transparent',
  },
  pressed: {
    opacity: 0.8,
    transform: [{ scale: 0.99 }],
  },
  disabled: {
    opacity: 0.5,
  },
  label: {
    fontSize: typography.button,
    fontWeight: '600',
    textAlign: 'center',
  },
  primaryLabel: {
    color: colors.white,
  },
  secondaryLabel: {
    color: colors.brand,
  },
  dangerLabel: {
    color: colors.error,
  },
  ghostLabel: {
    color: colors.brand,
  },
});

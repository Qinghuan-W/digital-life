import {
  forwardRef,
  ReactNode,
  useState,
} from 'react';
import {
  StyleProp,
  StyleSheet,
  Text,
  TextInput,
  TextInputProps,
  View,
  ViewStyle,
} from 'react-native';

import { colors, layout, radii, spacing, typography } from '@/constants/theme';

export type AppInputProps = TextInputProps & {
  label: string;
  error?: string;
  rightElement?: ReactNode;
  containerStyle?: StyleProp<ViewStyle>;
};

export const AppInput = forwardRef<TextInput, AppInputProps>(function AppInput(
  {
    label,
    error,
    rightElement,
    containerStyle,
    onBlur,
    onFocus,
    style,
    ...inputProps
  },
  ref,
) {
  const [focused, setFocused] = useState(false);

  return (
    <View style={[styles.field, containerStyle]}>
      <Text style={styles.label}>{label}</Text>
      <View
        style={[
          styles.inputShell,
          focused && styles.inputShellFocused,
          error && styles.inputShellError,
        ]}>
        <TextInput
          {...inputProps}
          accessibilityLabel={inputProps.accessibilityLabel ?? label}
          onBlur={(event) => {
            setFocused(false);
            onBlur?.(event);
          }}
          onFocus={(event) => {
            setFocused(true);
            onFocus?.(event);
          }}
          placeholderTextColor={colors.placeholder}
          ref={ref}
          selectionColor={colors.brand}
          style={[styles.input, style]}
        />
        {rightElement}
      </View>
      {error ? (
        <Text accessibilityLiveRegion="polite" style={styles.errorText}>
          {error}
        </Text>
      ) : null}
    </View>
  );
});

const styles = StyleSheet.create({
  field: {
    gap: spacing.x2,
  },
  label: {
    color: colors.text,
    fontSize: typography.helper,
    fontWeight: '600',
  },
  inputShell: {
    alignItems: 'center',
    backgroundColor: colors.input,
    borderColor: 'transparent',
    borderRadius: radii.input,
    borderWidth: 1.5,
    flexDirection: 'row',
    minHeight: layout.controlHeight,
    paddingHorizontal: spacing.x4,
  },
  inputShellFocused: {
    backgroundColor: colors.surface,
    borderColor: colors.brand,
  },
  inputShellError: {
    backgroundColor: colors.errorSoft,
    borderColor: colors.error,
  },
  input: {
    color: colors.text,
    flex: 1,
    fontSize: typography.body,
    minHeight: layout.controlHeight - 3,
    paddingVertical: 0,
  },
  errorText: {
    color: colors.error,
    fontSize: typography.caption,
    lineHeight: 18,
  },
});

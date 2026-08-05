import { forwardRef, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput } from 'react-native';

import { colors, layout, spacing, typography } from '@/constants/theme';

import { AppInput, AppInputProps } from './AppInput';

type PasswordInputProps = Omit<AppInputProps, 'rightElement' | 'secureTextEntry'>;

export const PasswordInput = forwardRef<TextInput, PasswordInputProps>(function PasswordInput(
  props,
  ref,
) {
  const [visible, setVisible] = useState(false);

  return (
    <AppInput
      {...props}
      ref={ref}
      rightElement={
        <Pressable
          accessibilityLabel={visible ? '隐藏密码' : '显示密码'}
          accessibilityRole="button"
          hitSlop={8}
          onPress={() => setVisible((current) => !current)}
          style={({ pressed }) => [styles.toggle, pressed && styles.togglePressed]}>
          <Text style={styles.toggleLabel}>{visible ? '隐藏' : '显示'}</Text>
        </Pressable>
      }
      secureTextEntry={!visible}
    />
  );
});

const styles = StyleSheet.create({
  toggle: {
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: spacing.x2,
    minHeight: layout.minimumTouchTarget,
    paddingHorizontal: spacing.x2,
  },
  togglePressed: {
    opacity: 0.55,
  },
  toggleLabel: {
    color: colors.brand,
    fontSize: typography.helper,
    fontWeight: '700',
  },
});

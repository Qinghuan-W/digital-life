import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { colors, layout, radii, spacing, typography } from '@/constants/theme';

type MessageComposerProps = {
  value: string;
  disabled?: boolean;
  onChangeText: (value: string) => void;
  onSend: () => void;
};

export function MessageComposer({ value, disabled = false, onChangeText, onSend }: MessageComposerProps) {
  const canSend = value.trim().length > 0 && !disabled;
  return (
    <View style={styles.container}>
      <TextInput
        accessibilityLabel="输入消息"
        editable={!disabled}
        maxLength={4000}
        multiline
        onChangeText={onChangeText}
        placeholder="输入消息…"
        placeholderTextColor={colors.placeholder}
        selectionColor={colors.brand}
        style={styles.input}
        textAlignVertical="center"
        value={value}
      />
      <Pressable
        accessibilityLabel="发送消息"
        accessibilityRole="button"
        accessibilityState={{ disabled: !canSend }}
        disabled={!canSend}
        onPress={onSend}
        style={({ pressed }) => [
          styles.sendButton,
          !canSend && styles.sendButtonDisabled,
          pressed && canSend && styles.pressed,
        ]}>
        <Text style={styles.sendText}>↑</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'flex-end',
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radii.card,
    borderWidth: 1,
    flexDirection: 'row',
    gap: spacing.x2,
    padding: spacing.x2,
  },
  input: {
    color: colors.text,
    flex: 1,
    fontSize: typography.body,
    maxHeight: 120,
    minHeight: layout.minimumTouchTarget,
    paddingHorizontal: spacing.x3,
    paddingVertical: spacing.x2,
  },
  sendButton: {
    alignItems: 'center',
    backgroundColor: colors.brand,
    borderRadius: radii.round,
    height: layout.minimumTouchTarget,
    justifyContent: 'center',
    width: layout.minimumTouchTarget,
  },
  sendButtonDisabled: { backgroundColor: colors.border },
  sendText: { color: colors.white, fontSize: 24, fontWeight: '700', lineHeight: 28 },
  pressed: { backgroundColor: colors.brandPressed, transform: [{ scale: 0.97 }] },
});

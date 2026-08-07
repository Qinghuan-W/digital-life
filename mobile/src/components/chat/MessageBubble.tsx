import { Pressable, StyleSheet, Text, View } from 'react-native';

import { colors, radii, spacing, typography } from '@/constants/theme';
import { Message } from '@/types/message';

type MessageBubbleProps = {
  message: Message;
  onRetry?: (message: Message) => void;
};

export function MessageBubble({ message, onRetry }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  return (
    <View style={[styles.row, isUser ? styles.userRow : styles.assistantRow]}>
      <View style={[styles.bubble, isUser ? styles.userBubble : styles.assistantBubble]}>
        <Text style={[styles.content, isUser && styles.userContent]}>{message.content}</Text>
        {message.deliveryState ? (
          <View style={styles.statusRow}>
            <Text style={[styles.status, isUser && styles.userStatus]}>
              {message.deliveryState === 'sending' ? '正在等待回复…' : '发送失败'}
            </Text>
            {message.deliveryState === 'failed' && onRetry ? (
              <Pressable
                accessibilityRole="button"
                hitSlop={8}
                onPress={() => onRetry(message)}>
                <Text style={styles.retry}>重试</Text>
              </Pressable>
            ) : null}
          </View>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', marginVertical: spacing.x1 },
  userRow: { justifyContent: 'flex-end' },
  assistantRow: { justifyContent: 'flex-start' },
  bubble: { borderRadius: radii.card, maxWidth: '82%', paddingHorizontal: spacing.x4, paddingVertical: spacing.x3 },
  userBubble: { backgroundColor: colors.brand, borderBottomRightRadius: 5 },
  assistantBubble: { backgroundColor: colors.surface, borderBottomLeftRadius: 5, borderColor: colors.border, borderWidth: 1 },
  content: { color: colors.text, fontSize: typography.body, lineHeight: 23 },
  userContent: { color: colors.white },
  statusRow: { alignItems: 'center', flexDirection: 'row', gap: spacing.x3, marginTop: spacing.x2 },
  status: { color: colors.placeholder, fontSize: 11 },
  userStatus: { color: '#D8EEE5' },
  retry: { color: '#FFD9D9', fontSize: 12, fontWeight: '800' },
});

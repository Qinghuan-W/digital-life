import { Pressable, StyleSheet, Text, View } from 'react-native';

import { colors, radii, spacing, typography } from '@/constants/theme';
import { Conversation } from '@/types/conversation';

type ConversationListItemProps = {
  conversation: Conversation;
  onPress: () => void;
};

export function ConversationListItem({ conversation, onPress }: ConversationListItemProps) {
  const initial = conversation.persona.displayName.trim().charAt(0).toUpperCase() || 'D';
  const preview = conversation.lastMessagePreview ?? '还没有消息，点击开始聊天';

  return (
    <Pressable
      accessibilityLabel={`与 ${conversation.persona.displayName} 的对话`}
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [styles.container, pressed && styles.pressed]}>
      <View style={styles.avatar}>
        <Text style={styles.avatarText}>{initial}</Text>
      </View>
      <View style={styles.content}>
        <View style={styles.titleRow}>
          <Text numberOfLines={1} style={styles.name}>
            {conversation.persona.displayName}
          </Text>
          <Text style={styles.time}>{formatConversationTime(conversation.lastMessageAt)}</Text>
        </View>
        <Text numberOfLines={1} style={styles.preview}>
          {preview}
        </Text>
      </View>
    </Pressable>
  );
}

function formatConversationTime(value: string | null): string {
  if (!value) {
    return '';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '';
  }
  const now = new Date();
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  }
  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' });
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderBottomColor: colors.border,
    borderBottomWidth: StyleSheet.hairlineWidth,
    flexDirection: 'row',
    gap: spacing.x4,
    minHeight: 94,
    paddingHorizontal: spacing.x4,
    paddingVertical: spacing.x3,
  },
  pressed: { backgroundColor: colors.brandSoft },
  avatar: {
    alignItems: 'center',
    backgroundColor: colors.brandSoft,
    borderRadius: radii.round,
    height: 52,
    justifyContent: 'center',
    width: 52,
  },
  avatarText: { color: colors.brand, fontSize: 20, fontWeight: '800' },
  content: { flex: 1, gap: 3 },
  titleRow: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between' },
  name: { color: colors.text, flex: 1, fontSize: typography.body, fontWeight: '700' },
  time: { color: colors.placeholder, fontSize: typography.caption, marginLeft: spacing.x2 },
  preview: { color: colors.textSecondary, fontSize: typography.helper },
});

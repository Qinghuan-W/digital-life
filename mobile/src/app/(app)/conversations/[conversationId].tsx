import { useLocalSearchParams, useRouter } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ChatEmptyState } from '@/components/chat/ChatEmptyState';
import { MessageBubble } from '@/components/chat/MessageBubble';
import { MessageComposer } from '@/components/chat/MessageComposer';
import { EditPersonaSheet } from '@/components/persona/EditPersonaSheet';
import { AppButton } from '@/components/ui/AppButton';
import { FormError } from '@/components/ui/FormError';
import { colors, layout, spacing, typography } from '@/constants/theme';
import {
  getConversation,
  getMessages,
  sendMessage,
} from '@/features/conversations/conversation-service';
import { getUserFacingError } from '@/services/api-errors';
import { ConversationDetail } from '@/types/conversation';
import { Message } from '@/types/message';

export default function ConversationScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ conversationId?: string | string[] }>();
  const conversationId = Array.isArray(params.conversationId)
    ? params.conversationId[0]
    : params.conversationId;
  const listRef = useRef<FlatList<Message>>(null);
  const sendingLock = useRef(false);
  const [conversation, setConversation] = useState<ConversationDetail>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [composerValue, setComposerValue] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [loadError, setLoadError] = useState<string>();
  const [sendError, setSendError] = useState<string>();
  const [editingPersona, setEditingPersona] = useState(false);

  const loadConversation = useCallback(async () => {
    if (!conversationId) {
      setLoadError('对话地址无效。');
      setLoading(false);
      return;
    }
    setLoading(true);
    setLoadError(undefined);
    try {
      const [detail, history] = await Promise.all([
        getConversation(conversationId),
        getMessages(conversationId),
      ]);
      if (history.length > 0) {
        const last = history[history.length - 1];
        if (last.role === 'user' && last.clientMessageId) {
          history[history.length - 1] = { ...last, deliveryState: 'failed' };
        }
      }
      setConversation(detail);
      setMessages(history);
    } catch (error) {
      setLoadError(getUserFacingError(error));
    } finally {
      setLoading(false);
    }
  }, [conversationId]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      void loadConversation();
    }, 0);
    return () => clearTimeout(timeoutId);
  }, [loadConversation]);

  const leaveConversation = () => {
    if (router.canGoBack()) {
      router.back();
    } else {
      router.replace('/(app)');
    }
  };

  const performSend = async (content: string, clientMessageId: string) => {
    if (!conversationId || sendingLock.current) {
      return;
    }
    sendingLock.current = true;
    setSending(true);
    setSendError(undefined);
    const now = new Date().toISOString();
    setMessages((current) => {
      const existing = current.find((item) => item.clientMessageId === clientMessageId);
      if (existing) {
        return current.map((item) =>
          item.clientMessageId === clientMessageId
            ? { ...item, deliveryState: 'sending' }
            : item,
        );
      }
      return [
        ...current,
        {
          id: `local-${clientMessageId}`,
          conversationId,
          role: 'user',
          content,
          status: 'completed',
          clientMessageId,
          createdAt: now,
          updatedAt: now,
          deliveryState: 'sending',
        },
      ];
    });

    try {
      const result = await sendMessage(conversationId, content, clientMessageId);
      setMessages((current) => [
        ...current.filter((item) => item.clientMessageId !== clientMessageId),
        result.userMessage,
        result.assistantMessage,
      ]);
    } catch (error) {
      setSendError(getUserFacingError(error));
      setMessages((current) =>
        current.map((item) =>
          item.clientMessageId === clientMessageId
            ? { ...item, deliveryState: 'failed' }
            : item,
        ),
      );
    } finally {
      sendingLock.current = false;
      setSending(false);
    }
  };

  const sendNewMessage = () => {
    const content = composerValue.trim();
    if (!content || sendingLock.current) {
      return;
    }
    const clientMessageId = createClientMessageId();
    setComposerValue('');
    void performSend(content, clientMessageId);
  };

  const retryMessage = (message: Message) => {
    if (message.clientMessageId && !sendingLock.current) {
      void performSend(message.content, message.clientMessageId);
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.centerState}>
          <ActivityIndicator color={colors.brand} />
          <Text style={styles.loadingText}>正在加载对话</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!conversation || loadError) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.errorPage}>
          <Text style={styles.errorTitle}>无法打开对话</Text>
          <Text style={styles.errorDescription}>{loadError ?? '对话不存在。'}</Text>
          <AppButton onPress={() => void loadConversation()} title="重试" />
          <AppButton onPress={leaveConversation} title="返回首页" variant="ghost" />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView edges={['top', 'right', 'bottom', 'left']} style={styles.safeArea}>
      <View style={styles.page}>
        <View style={styles.header}>
          <Pressable
            accessibilityLabel="返回对话列表"
            accessibilityRole="button"
            onPress={leaveConversation}
            style={({ pressed }) => [styles.backButton, pressed && styles.pressed]}>
            <Text style={styles.backIcon}>←</Text>
          </Pressable>
          <View style={styles.headerCopy}>
            <Text numberOfLines={1} style={styles.headerTitle}>
              {conversation.persona.displayName}
            </Text>
          </View>
          <Pressable
            accessibilityLabel="编辑 Persona"
            accessibilityRole="button"
            onPress={() => setEditingPersona(true)}
            style={({ pressed }) => [styles.backButton, pressed && styles.pressed]}>
            <Text style={styles.infoIcon}>•••</Text>
          </Pressable>
        </View>

        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          enabled={Platform.OS === 'ios'}
          style={styles.keyboardView}>
          <FlatList
            contentContainerStyle={[
              styles.messageContent,
              messages.length === 0 && styles.emptyMessageContent,
            ]}
            data={messages}
            keyExtractor={(item) => item.id}
            keyboardDismissMode={Platform.OS === 'ios' ? 'interactive' : 'on-drag'}
            keyboardShouldPersistTaps="handled"
            ListEmptyComponent={<ChatEmptyState personaName={conversation.persona.displayName} />}
            onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
            ref={listRef}
            renderItem={({ item }) => <MessageBubble message={item} onRetry={retryMessage} />}
            showsVerticalScrollIndicator={false}
            style={styles.messageList}
          />

          <View style={styles.composerArea}>
            <FormError message={sendError} />
            <MessageComposer
              disabled={sending}
              onChangeText={(value) => {
                setComposerValue(value);
                setSendError(undefined);
              }}
              onSend={sendNewMessage}
              value={composerValue}
            />
          </View>
        </KeyboardAvoidingView>
        {editingPersona ? (
          <EditPersonaSheet
            onClose={() => setEditingPersona(false)}
            onUpdated={(persona) => {
              setConversation((current) =>
                current ? { ...current, title: persona.displayName, persona } : current,
              );
            }}
            persona={conversation.persona}
            visible
          />
        ) : null}
      </View>
    </SafeAreaView>
  );
}

function createClientMessageId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (character) => {
    const random = Math.floor(Math.random() * 16);
    const value = character === 'x' ? random : (random & 0x3) | 0x8;
    return value.toString(16);
  });
}

const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.background, flex: 1 },
  keyboardView: { flex: 1 },
  page: { alignSelf: 'center', flex: 1, maxWidth: layout.maxContentWidth, width: '100%' },
  header: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderBottomColor: colors.border,
    borderBottomWidth: StyleSheet.hairlineWidth,
    flexDirection: 'row',
    minHeight: 66,
    paddingHorizontal: spacing.x3,
  },
  backButton: { alignItems: 'center', height: layout.minimumTouchTarget, justifyContent: 'center', width: layout.minimumTouchTarget },
  backIcon: { color: colors.text, fontSize: 25 },
  infoIcon: { color: colors.textSecondary, fontSize: 16, fontWeight: '800', letterSpacing: 1 },
  headerCopy: { alignItems: 'center', flex: 1 },
  headerTitle: { color: colors.text, fontSize: typography.body, fontWeight: '800' },
  pressed: { opacity: 0.5 },
  messageList: { flex: 1 },
  messageContent: { paddingHorizontal: spacing.x4, paddingVertical: spacing.x4 },
  emptyMessageContent: { flexGrow: 1, justifyContent: 'center' },
  composerArea: {
    backgroundColor: colors.background,
    borderTopColor: colors.border,
    borderTopWidth: StyleSheet.hairlineWidth,
    gap: spacing.x2,
    paddingHorizontal: spacing.x3,
    paddingVertical: spacing.x2,
  },
  centerState: { alignItems: 'center', flex: 1, justifyContent: 'center' },
  loadingText: { color: colors.textSecondary, fontSize: typography.helper, marginTop: spacing.x3 },
  errorPage: { flex: 1, gap: spacing.x4, justifyContent: 'center', paddingHorizontal: layout.pagePadding },
  errorTitle: { color: colors.text, fontSize: typography.pageTitle, fontWeight: '800', textAlign: 'center' },
  errorDescription: { color: colors.textSecondary, fontSize: typography.helper, lineHeight: 21, textAlign: 'center' },
});

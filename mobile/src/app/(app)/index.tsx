import { useFocusEffect, useRouter } from 'expo-router';
import { useCallback, useRef, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ChatEmptyState } from '@/components/chat/ChatEmptyState';
import { ConversationListItem } from '@/components/chat/ConversationListItem';
import { CreatePersonaSheet } from '@/components/persona/CreatePersonaSheet';
import { AppButton } from '@/components/ui/AppButton';
import { BrandMark } from '@/components/ui/BrandMark';
import { LoadingScreen } from '@/components/ui/LoadingScreen';
import { colors, layout, radii, spacing, typography } from '@/constants/theme';
import { useAuth } from '@/features/auth/auth-context';
import { getConversations } from '@/features/conversations/conversation-service';
import { getUserFacingError } from '@/services/api-errors';
import { Conversation, PersonaCreationResult } from '@/types/conversation';

export default function HomeScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const loadedOnce = useRef(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string>();
  const [createSheetVisible, setCreateSheetVisible] = useState(false);

  const loadConversationList = useCallback(async (showInitialLoading: boolean) => {
    if (showInitialLoading && !loadedOnce.current) {
      setLoading(true);
    }
    setError(undefined);
    try {
      setConversations(await getConversations());
      loadedOnce.current = true;
    } catch (requestError) {
      setError(getUserFacingError(requestError));
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      void loadConversationList(true);
    }, [loadConversationList]),
  );

  if (!user) {
    return <LoadingScreen />;
  }

  const initial = user.displayName.trim().charAt(0).toUpperCase() || 'D';

  const refresh = async () => {
    setRefreshing(true);
    try {
      await loadConversationList(false);
    } finally {
      setRefreshing(false);
    }
  };

  const openConversation = (conversationId: string) => {
    router.push({
      pathname: '/(app)/conversations/[conversationId]',
      params: { conversationId },
    });
  };

  const personaCreated = (result: PersonaCreationResult) => {
    setConversations((current) => [
      result.conversation,
      ...current.filter((item) => item.id !== result.conversation.id),
    ]);
    setCreateSheetVisible(false);
    requestAnimationFrame(() => openConversation(result.conversation.id));
  };

  return (
    <SafeAreaView edges={['top', 'right', 'bottom', 'left']} style={styles.safeArea}>
      <View style={styles.page}>
        <View style={styles.header}>
          <View style={styles.brandRow}>
            <BrandMark size={40} />
            <Text style={styles.brandName}>DigitalLife</Text>
          </View>
          <Pressable
            accessibilityLabel="进入个人资料"
            accessibilityRole="button"
            onPress={() => router.push('/(app)/profile')}
            style={({ pressed }) => [styles.avatar, pressed && styles.pressed]}>
            <Text style={styles.avatarText}>{initial}</Text>
          </Pressable>
        </View>

        <View style={styles.titleBlock}>
          <Text style={styles.eyebrow}>YOUR DIGITAL LIFE</Text>
          <Text style={styles.title}>对话</Text>
            <Text style={styles.subtitle}>让每段对话自然延续。</Text>
        </View>

        {loading ? (
          <View style={styles.centerState}>
            <ActivityIndicator color={colors.brand} />
            <Text style={styles.stateText}>正在加载对话</Text>
          </View>
        ) : error && conversations.length === 0 ? (
          <View style={styles.centerState}>
            <Text style={styles.errorTitle}>暂时无法加载对话</Text>
            <Text style={styles.stateText}>{error}</Text>
            <View style={styles.retryAction}>
              <AppButton onPress={() => void loadConversationList(true)} title="重新加载" />
            </View>
          </View>
        ) : (
          <FlatList
            contentContainerStyle={[
              styles.listContent,
              conversations.length === 0 && styles.emptyListContent,
            ]}
            data={conversations}
            keyExtractor={(item) => item.id}
            ListEmptyComponent={
              <ChatEmptyState onCreate={() => setCreateSheetVisible(true)} />
            }
            refreshControl={
              <RefreshControl
                colors={[colors.brand]}
                onRefresh={() => void refresh()}
                refreshing={refreshing}
                tintColor={colors.brand}
              />
            }
            renderItem={({ item }) => (
              <ConversationListItem
                conversation={item}
                onPress={() => openConversation(item.id)}
              />
            )}
            showsVerticalScrollIndicator={false}
            style={styles.list}
          />
        )}

        <Pressable
          accessibilityLabel="创建 Persona"
          accessibilityRole="button"
          onPress={() => setCreateSheetVisible(true)}
          style={({ pressed }) => [styles.fab, pressed && styles.fabPressed]}>
          <Text style={styles.fabText}>+</Text>
        </Pressable>
      </View>

      <CreatePersonaSheet
        onClose={() => setCreateSheetVisible(false)}
        onCreated={personaCreated}
        visible={createSheetVisible}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.background, flex: 1 },
  page: { alignSelf: 'center', flex: 1, maxWidth: layout.maxContentWidth, width: '100%' },
  header: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: layout.pagePadding,
    paddingTop: spacing.x4,
  },
  brandRow: { alignItems: 'center', flexDirection: 'row', gap: spacing.x3 },
  brandName: { color: colors.text, fontSize: typography.sectionTitle, fontWeight: '700' },
  avatar: {
    alignItems: 'center',
    backgroundColor: colors.brandSoft,
    borderColor: colors.border,
    borderRadius: 22,
    borderWidth: 1,
    height: layout.minimumTouchTarget,
    justifyContent: 'center',
    width: layout.minimumTouchTarget,
  },
  avatarText: { color: colors.brand, fontSize: typography.body, fontWeight: '800' },
  pressed: { opacity: 0.6 },
  titleBlock: { paddingHorizontal: layout.pagePadding, paddingBottom: spacing.x4, paddingTop: spacing.x8 },
  eyebrow: { color: colors.brand, fontSize: 11, fontWeight: '800', letterSpacing: 1.3 },
  title: { color: colors.text, fontSize: typography.pageTitle, fontWeight: '800', marginTop: spacing.x2 },
  subtitle: { color: colors.textSecondary, fontSize: typography.helper, marginTop: spacing.x1 },
  list: { flex: 1 },
  listContent: { paddingBottom: 96, paddingHorizontal: layout.pagePadding },
  emptyListContent: { flexGrow: 1, justifyContent: 'center' },
  centerState: { alignItems: 'center', flex: 1, justifyContent: 'center', padding: spacing.x8 },
  stateText: { color: colors.textSecondary, fontSize: typography.helper, lineHeight: 21, marginTop: spacing.x3, textAlign: 'center' },
  errorTitle: { color: colors.text, fontSize: typography.sectionTitle, fontWeight: '700' },
  retryAction: { marginTop: spacing.x5, minWidth: 180 },
  fab: {
    alignItems: 'center',
    backgroundColor: colors.brand,
    borderRadius: radii.round,
    bottom: spacing.x5,
    elevation: 6,
    height: 58,
    justifyContent: 'center',
    position: 'absolute',
    right: layout.pagePadding,
    shadowColor: '#0B2F21',
    shadowOffset: { height: 4, width: 0 },
    shadowOpacity: 0.22,
    shadowRadius: 8,
    width: 58,
  },
  fabPressed: { backgroundColor: colors.brandPressed, transform: [{ scale: 0.96 }] },
  fabText: { color: colors.white, fontSize: 31, fontWeight: '400', lineHeight: 34 },
});

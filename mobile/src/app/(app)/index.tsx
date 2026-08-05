import { useRouter } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { AppButton } from '@/components/ui/AppButton';
import { BrandMark } from '@/components/ui/BrandMark';
import { LoadingScreen } from '@/components/ui/LoadingScreen';
import { PageContainer } from '@/components/ui/PageContainer';
import { colors, layout, radii, spacing, typography } from '@/constants/theme';
import { useAuth } from '@/features/auth/auth-context';

const PREVIEWS = [
  { marker: '01', title: '与专属 Persona 聊天', description: '建立属于你的长期陪伴关系' },
  { marker: '02', title: '保存共同记忆', description: '让重要经历自然延续' },
  { marker: '03', title: '管理日程与提醒', description: '轻松照顾生活中的每件事' },
] as const;

export default function HomeScreen() {
  const router = useRouter();
  const { user } = useAuth();

  if (!user) {
    return <LoadingScreen />;
  }

  const initial = user.displayName.trim().charAt(0).toUpperCase() || 'D';

  return (
    <PageContainer contentStyle={styles.page} scroll>
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

      <View style={styles.welcome}>
        <Text style={styles.eyebrow}>WELCOME BACK</Text>
        <Text style={styles.title}>欢迎回来，{user.displayName}</Text>
        <Text style={styles.subtitle}>你的私人 AI 伙伴正在准备中。</Text>
      </View>

      <View style={styles.previewSection}>
        <Text style={styles.sectionTitle}>接下来，我们会一起完成</Text>
        <View style={styles.previewList}>
          {PREVIEWS.map((preview) => (
            <View key={preview.marker} style={styles.previewItem}>
              <View style={styles.marker}>
                <Text style={styles.markerText}>{preview.marker}</Text>
              </View>
              <View style={styles.previewCopy}>
                <Text style={styles.previewTitle}>{preview.title}</Text>
                <Text style={styles.previewDescription}>{preview.description}</Text>
              </View>
            </View>
          ))}
        </View>
      </View>

      <View style={styles.bottomAction}>
        <AppButton onPress={() => undefined} title="Continue building DigitalLife" />
        <Text style={styles.phaseNote}>Phase 1B-2 · 真实账号已连接</Text>
      </View>
    </PageContainer>
  );
}

const styles = StyleSheet.create({
  page: {
    paddingHorizontal: layout.pagePadding,
    paddingVertical: spacing.x5,
  },
  header: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  brandRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: spacing.x3,
  },
  brandName: {
    color: colors.text,
    fontSize: typography.sectionTitle,
    fontWeight: '700',
  },
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
  avatarText: {
    color: colors.brand,
    fontSize: typography.body,
    fontWeight: '800',
  },
  pressed: {
    opacity: 0.6,
  },
  welcome: {
    marginTop: spacing.x10,
  },
  eyebrow: {
    color: colors.brand,
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 1.4,
  },
  title: {
    color: colors.text,
    fontSize: typography.pageTitle,
    fontWeight: '800',
    letterSpacing: -0.6,
    lineHeight: 36,
    marginTop: spacing.x3,
  },
  subtitle: {
    color: colors.textSecondary,
    fontSize: typography.body,
    lineHeight: 24,
    marginTop: spacing.x2,
  },
  previewSection: {
    marginTop: spacing.x10,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: typography.sectionTitle,
    fontWeight: '700',
  },
  previewList: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radii.card,
    borderWidth: 1,
    marginTop: spacing.x4,
    overflow: 'hidden',
  },
  previewItem: {
    alignItems: 'center',
    borderBottomColor: colors.border,
    borderBottomWidth: StyleSheet.hairlineWidth,
    flexDirection: 'row',
    gap: spacing.x4,
    minHeight: 82,
    paddingHorizontal: spacing.x4,
    paddingVertical: spacing.x3,
  },
  marker: {
    alignItems: 'center',
    backgroundColor: colors.brandSoft,
    borderRadius: radii.small,
    height: 38,
    justifyContent: 'center',
    width: 38,
  },
  markerText: {
    color: colors.brand,
    fontSize: typography.caption,
    fontWeight: '800',
  },
  previewCopy: {
    flex: 1,
    gap: spacing.x1,
  },
  previewTitle: {
    color: colors.text,
    fontSize: typography.body,
    fontWeight: '600',
  },
  previewDescription: {
    color: colors.textSecondary,
    fontSize: typography.helper,
    lineHeight: 20,
  },
  bottomAction: {
    gap: spacing.x3,
    marginTop: spacing.x8,
    paddingBottom: spacing.x2,
  },
  phaseNote: {
    color: colors.placeholder,
    fontSize: typography.caption,
    textAlign: 'center',
  },
});

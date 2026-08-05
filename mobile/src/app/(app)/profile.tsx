import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { AppButton } from '@/components/ui/AppButton';
import { AppInput } from '@/components/ui/AppInput';
import { LoadingScreen } from '@/components/ui/LoadingScreen';
import { PageContainer } from '@/components/ui/PageContainer';
import { colors, layout, radii, spacing, typography } from '@/constants/theme';
import { useAuth } from '@/features/auth/auth-context';
import { validateDisplayName } from '@/features/auth/validation';

export default function ProfileScreen() {
  const router = useRouter();
  const { logout, updateProfile, user } = useAuth();
  const [displayName, setDisplayName] = useState(user?.displayName ?? '');
  const [nameError, setNameError] = useState<string>();
  const [savedMessage, setSavedMessage] = useState<string>();
  const [saving, setSaving] = useState(false);

  if (!user) {
    return <LoadingScreen />;
  }

  const initial = user.displayName.trim().charAt(0).toUpperCase() || 'D';

  const saveProfile = async () => {
    const error = validateDisplayName(displayName);
    setNameError(error);
    setSavedMessage(undefined);

    if (error) {
      return;
    }

    setSaving(true);
    try {
      await updateProfile(displayName);
      setSavedMessage('显示名称已更新到本次 Mock 会话。');
    } finally {
      setSaving(false);
    }
  };

  const signOut = () => {
    logout();
  };

  return (
    <PageContainer contentStyle={styles.page} keyboardAware scroll>
      <View style={styles.header}>
        <Pressable
          accessibilityLabel="返回首页"
          accessibilityRole="button"
          onPress={() => (router.canGoBack() ? router.back() : router.replace('/(app)'))}
          style={({ pressed }) => [styles.backButton, pressed && styles.pressed]}>
          <Text allowFontScaling={false} style={styles.backIcon}>
            ←
          </Text>
        </Pressable>
        <Text style={styles.headerTitle}>个人资料</Text>
        <View style={styles.backButton} />
      </View>

      <View style={styles.identity}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{initial}</Text>
        </View>
        <Text style={styles.name}>{user.displayName}</Text>
        <Text style={styles.email}>{user.email}</Text>
        <View style={styles.statusBadge}>
          <View style={styles.statusDot} />
          <Text style={styles.statusText}>Mock 会话已登录</Text>
        </View>
      </View>

      <View style={styles.details}>
        <Text style={styles.sectionTitle}>账号信息</Text>
        <View style={styles.infoCard}>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>邮箱</Text>
            <Text style={styles.infoValue}>{user.email}</Text>
          </View>
          <View style={[styles.infoRow, styles.infoRowLast]}>
            <Text style={styles.infoLabel}>账号状态</Text>
            <Text style={styles.infoValue}>仅限前端 Mock</Text>
          </View>
        </View>
      </View>

      <View style={styles.editSection}>
        <Text style={styles.sectionTitle}>编辑资料</Text>
        <AppInput
          autoCapitalize="words"
          autoComplete="name"
          error={nameError}
          label="显示名称"
          onChangeText={(value) => {
            setDisplayName(value);
            setNameError(undefined);
            setSavedMessage(undefined);
          }}
          onSubmitEditing={saveProfile}
          returnKeyType="done"
          value={displayName}
        />
        {savedMessage ? (
          <Text accessibilityLiveRegion="polite" style={styles.savedMessage}>
            {savedMessage}
          </Text>
        ) : null}
        <AppButton loading={saving} onPress={saveProfile} title="保存修改" />
      </View>

      <View style={styles.logoutSection}>
        <AppButton onPress={signOut} title="退出登录" variant="danger" />
        <Text style={styles.logoutNote}>退出只会清除当前内存中的 Mock 状态。</Text>
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
  backButton: {
    alignItems: 'center',
    height: layout.minimumTouchTarget,
    justifyContent: 'center',
    width: layout.minimumTouchTarget,
  },
  backIcon: {
    color: colors.text,
    fontSize: 25,
  },
  pressed: {
    opacity: 0.5,
  },
  headerTitle: {
    color: colors.text,
    fontSize: typography.sectionTitle,
    fontWeight: '700',
  },
  identity: {
    alignItems: 'center',
    marginTop: spacing.x8,
  },
  avatar: {
    alignItems: 'center',
    backgroundColor: colors.brand,
    borderRadius: 38,
    height: 76,
    justifyContent: 'center',
    width: 76,
  },
  avatarText: {
    color: colors.white,
    fontSize: 28,
    fontWeight: '800',
  },
  name: {
    color: colors.text,
    fontSize: 22,
    fontWeight: '700',
    marginTop: spacing.x4,
  },
  email: {
    color: colors.textSecondary,
    fontSize: typography.helper,
    marginTop: spacing.x1,
  },
  statusBadge: {
    alignItems: 'center',
    backgroundColor: colors.brandSoft,
    borderRadius: radii.small,
    flexDirection: 'row',
    gap: spacing.x2,
    marginTop: spacing.x3,
    paddingHorizontal: spacing.x3,
    paddingVertical: spacing.x2,
  },
  statusDot: {
    backgroundColor: colors.success,
    borderRadius: 4,
    height: 8,
    width: 8,
  },
  statusText: {
    color: colors.success,
    fontSize: typography.caption,
    fontWeight: '700',
  },
  details: {
    marginTop: spacing.x8,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: typography.sectionTitle,
    fontWeight: '700',
  },
  infoCard: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radii.card,
    borderWidth: 1,
    marginTop: spacing.x3,
    paddingHorizontal: spacing.x4,
  },
  infoRow: {
    borderBottomColor: colors.border,
    borderBottomWidth: StyleSheet.hairlineWidth,
    gap: spacing.x2,
    paddingVertical: spacing.x4,
  },
  infoRowLast: {
    borderBottomWidth: 0,
  },
  infoLabel: {
    color: colors.textSecondary,
    fontSize: typography.caption,
  },
  infoValue: {
    color: colors.text,
    fontSize: typography.body,
    fontWeight: '600',
  },
  editSection: {
    gap: spacing.x3,
    marginTop: spacing.x8,
  },
  savedMessage: {
    color: colors.success,
    fontSize: typography.helper,
    lineHeight: 20,
  },
  logoutSection: {
    gap: spacing.x3,
    marginTop: spacing.x10,
    paddingBottom: spacing.x3,
  },
  logoutNote: {
    color: colors.placeholder,
    fontSize: typography.caption,
    textAlign: 'center',
  },
});

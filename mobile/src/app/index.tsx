import { Redirect, useRouter } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { AppButton } from '@/components/ui/AppButton';
import { BrandMark } from '@/components/ui/BrandMark';
import { LoadingScreen } from '@/components/ui/LoadingScreen';
import { PageContainer } from '@/components/ui/PageContainer';
import { colors, layout, spacing, typography } from '@/constants/theme';
import { useAuth } from '@/features/auth/auth-context';

export default function WelcomeScreen() {
  const router = useRouter();
  const { completeWelcome, hasSeenWelcome, status } = useAuth();

  if (status === 'loading') {
    return <LoadingScreen />;
  }

  if (status === 'authenticated') {
    return <Redirect href="/(app)" />;
  }

  if (hasSeenWelcome) {
    return <Redirect href="/(auth)/login" />;
  }

  const openLogin = () => {
    completeWelcome();
    router.push('/(auth)/login');
  };

  return (
    <PageContainer contentStyle={styles.page}>
      <View style={styles.brandRow}>
        <BrandMark size={48} />
        <Text style={styles.brandName}>DigitalLife</Text>
      </View>

      <View style={styles.hero}>
        <BrandMark size={88} />
        <Text style={styles.title}>DigitalLife</Text>
        <Text style={styles.englishCopy}>
          A companion that remembers,{`\n`}understands and grows with you.
        </Text>
        <Text style={styles.chineseCopy}>
          一个理解你、记得你，{`\n`}并陪你一起生活的 AI 伙伴。
        </Text>
      </View>

      <View style={styles.actions}>
        <AppButton onPress={openLogin} title="开始使用" />
        <View style={styles.loginRow}>
          <Text style={styles.loginPrompt}>已有账号？</Text>
          <Pressable
            accessibilityRole="button"
            hitSlop={8}
            onPress={openLogin}
            style={({ pressed }) => pressed && styles.linkPressed}>
            <Text style={styles.loginLink}>登录</Text>
          </Pressable>
        </View>
      </View>
    </PageContainer>
  );
}

const styles = StyleSheet.create({
  page: {
    paddingHorizontal: layout.pagePadding,
    paddingVertical: spacing.x5,
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
    letterSpacing: -0.2,
  },
  hero: {
    alignItems: 'center',
    flex: 1,
    justifyContent: 'center',
    paddingBottom: spacing.x8,
  },
  title: {
    color: colors.text,
    fontSize: typography.brandTitle,
    fontWeight: '800',
    letterSpacing: -0.8,
    marginTop: spacing.x6,
  },
  englishCopy: {
    color: colors.text,
    fontSize: 18,
    fontWeight: '600',
    lineHeight: 26,
    marginTop: spacing.x5,
    textAlign: 'center',
  },
  chineseCopy: {
    color: colors.textSecondary,
    fontSize: typography.body,
    lineHeight: 25,
    marginTop: spacing.x3,
    textAlign: 'center',
  },
  actions: {
    gap: spacing.x4,
  },
  loginRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
    minHeight: layout.minimumTouchTarget,
  },
  loginPrompt: {
    color: colors.textSecondary,
    fontSize: typography.helper,
  },
  loginLink: {
    color: colors.brand,
    fontSize: typography.helper,
    fontWeight: '700',
  },
  linkPressed: {
    opacity: 0.55,
  },
});

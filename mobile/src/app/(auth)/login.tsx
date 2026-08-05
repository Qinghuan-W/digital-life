import { useRouter } from 'expo-router';
import { useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { AppButton } from '@/components/ui/AppButton';
import { AppInput } from '@/components/ui/AppInput';
import { AuthHeader } from '@/components/ui/AuthHeader';
import { FormError } from '@/components/ui/FormError';
import { PageContainer } from '@/components/ui/PageContainer';
import { PasswordInput } from '@/components/ui/PasswordInput';
import { colors, layout, spacing, typography } from '@/constants/theme';
import { useAuth } from '@/features/auth/auth-context';
import {
  hasValidationErrors,
  LoginFieldErrors,
  validateLoginForm,
} from '@/features/auth/validation';

export default function LoginScreen() {
  const router = useRouter();
  const { login, returnToWelcome } = useAuth();
  const passwordRef = useRef<TextInput>(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<LoginFieldErrors>({});
  const [formError, setFormError] = useState<string>();
  const [submitting, setSubmitting] = useState(false);

  const goBack = () => {
    returnToWelcome();
    router.replace('/');
  };

  const submit = async () => {
    const values = { email, password };
    const nextErrors = validateLoginForm(values);
    setErrors(nextErrors);
    setFormError(undefined);

    if (hasValidationErrors(nextErrors)) {
      setFormError('请检查标注的输入项后再登录。');
      return;
    }

    setSubmitting(true);
    try {
      await login(values);
    } catch {
      setFormError('Mock 登录暂时无法完成，请重试。');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PageContainer contentStyle={styles.page} keyboardAware scroll>
      <AuthHeader
        onBack={goBack}
        subtitle="登录后继续与你的 AI 伙伴对话"
        title="欢迎回来"
      />

      <View style={styles.form}>
        <FormError message={formError} />
        <AppInput
          autoCapitalize="none"
          autoComplete="email"
          autoCorrect={false}
          autoFocus
          blurOnSubmit={false}
          error={errors.email}
          keyboardType="email-address"
          label="邮箱"
          onChangeText={(value) => {
            setEmail(value);
            setErrors((current) => ({ ...current, email: undefined }));
          }}
          onSubmitEditing={() => passwordRef.current?.focus()}
          placeholder="user@example.com"
          returnKeyType="next"
          textContentType="emailAddress"
          value={email}
        />
        <PasswordInput
          autoComplete="current-password"
          error={errors.password}
          label="密码"
          onChangeText={(value) => {
            setPassword(value);
            setErrors((current) => ({ ...current, password: undefined }));
          }}
          onSubmitEditing={submit}
          placeholder="至少 8 位"
          ref={passwordRef}
          returnKeyType="done"
          textContentType="password"
          value={password}
        />
        <AppButton loading={submitting} onPress={submit} title="登录" />
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>还没有账号？</Text>
        <Pressable
          accessibilityRole="button"
          hitSlop={8}
          onPress={() => router.push('/(auth)/register')}
          style={({ pressed }) => pressed && styles.pressed}>
          <Text style={styles.footerLink}>创建账号</Text>
        </Pressable>
      </View>

      <Text style={styles.mockNote}>Phase 1A · 当前使用临时 Mock 登录</Text>
    </PageContainer>
  );
}

const styles = StyleSheet.create({
  page: {
    paddingHorizontal: layout.pagePadding,
    paddingVertical: spacing.x5,
  },
  form: {
    gap: spacing.x4,
    marginTop: spacing.x8,
  },
  footer: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: spacing.x6,
    minHeight: layout.minimumTouchTarget,
  },
  footerText: {
    color: colors.textSecondary,
    fontSize: typography.helper,
  },
  footerLink: {
    color: colors.brand,
    fontSize: typography.helper,
    fontWeight: '700',
  },
  mockNote: {
    color: colors.placeholder,
    fontSize: typography.caption,
    marginTop: 'auto',
    paddingTop: spacing.x8,
    textAlign: 'center',
  },
  pressed: {
    opacity: 0.55,
  },
});

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
  RegisterFieldErrors,
  validateRegisterForm,
} from '@/features/auth/validation';

export default function RegisterScreen() {
  const router = useRouter();
  const { register } = useAuth();
  const emailRef = useRef<TextInput>(null);
  const passwordRef = useRef<TextInput>(null);
  const confirmPasswordRef = useRef<TextInput>(null);
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<RegisterFieldErrors>({});
  const [formError, setFormError] = useState<string>();
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    const values = { displayName, email, password, confirmPassword };
    const nextErrors = validateRegisterForm(values);
    setErrors(nextErrors);
    setFormError(undefined);

    if (hasValidationErrors(nextErrors)) {
      setFormError('请完成所有必填项并修正输入内容。');
      return;
    }

    setSubmitting(true);
    try {
      await register({ displayName, email, password });
    } catch {
      setFormError('Mock 注册暂时无法完成，请重试。');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PageContainer contentStyle={styles.page} keyboardAware scroll>
      <AuthHeader
        onBack={() => router.replace('/(auth)/login')}
        subtitle="先创建一个临时资料，稍后再接入真实账号系统"
        title="创建账号"
      />

      <View style={styles.form}>
        <FormError message={formError} />
        <AppInput
          autoCapitalize="words"
          autoComplete="name"
          autoFocus
          blurOnSubmit={false}
          error={errors.displayName}
          label="显示名称"
          onChangeText={(value) => {
            setDisplayName(value);
            setErrors((current) => ({ ...current, displayName: undefined }));
          }}
          onSubmitEditing={() => emailRef.current?.focus()}
          placeholder="你希望被怎样称呼"
          returnKeyType="next"
          textContentType="name"
          value={displayName}
        />
        <AppInput
          autoCapitalize="none"
          autoComplete="email"
          autoCorrect={false}
          blurOnSubmit={false}
          error={errors.email}
          keyboardType="email-address"
          label="邮箱"
          onChangeText={(value) => {
            setEmail(value);
            setErrors((current) => ({ ...current, email: undefined }));
          }}
          onSubmitEditing={() => passwordRef.current?.focus()}
          placeholder="name@example.com"
          ref={emailRef}
          returnKeyType="next"
          textContentType="emailAddress"
          value={email}
        />
        <PasswordInput
          autoComplete="new-password"
          blurOnSubmit={false}
          error={errors.password}
          label="密码"
          onChangeText={(value) => {
            setPassword(value);
            setErrors((current) => ({ ...current, password: undefined }));
          }}
          onSubmitEditing={() => confirmPasswordRef.current?.focus()}
          placeholder="至少 8 位"
          ref={passwordRef}
          returnKeyType="next"
          textContentType="newPassword"
          value={password}
        />
        <PasswordInput
          autoComplete="new-password"
          error={errors.confirmPassword}
          label="确认密码"
          onChangeText={(value) => {
            setConfirmPassword(value);
            setErrors((current) => ({ ...current, confirmPassword: undefined }));
          }}
          onSubmitEditing={submit}
          placeholder="再次输入密码"
          ref={confirmPasswordRef}
          returnKeyType="done"
          textContentType="newPassword"
          value={confirmPassword}
        />
        <AppButton loading={submitting} onPress={submit} title="注册并继续" />
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>已经有账号？</Text>
        <Pressable
          accessibilityRole="button"
          hitSlop={8}
          onPress={() => router.replace('/(auth)/login')}
          style={({ pressed }) => pressed && styles.pressed}>
          <Text style={styles.footerLink}>登录</Text>
        </Pressable>
      </View>
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
  pressed: {
    opacity: 0.55,
  },
});

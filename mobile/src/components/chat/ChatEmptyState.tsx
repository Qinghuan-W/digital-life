import { StyleSheet, Text, View } from 'react-native';

import { AppButton } from '@/components/ui/AppButton';
import { BrandMark } from '@/components/ui/BrandMark';
import { colors, spacing, typography } from '@/constants/theme';

type ChatEmptyStateProps = {
  personaName?: string;
  onCreate?: () => void;
};

export function ChatEmptyState({ personaName, onCreate }: ChatEmptyStateProps) {
  return (
    <View style={styles.container}>
      <BrandMark size={58} />
      <Text style={styles.title}>
        {personaName ? `开始和 ${personaName} 聊天` : '创建你的第一个 Persona'}
      </Text>
      <Text style={styles.description}>
        {personaName
          ? '这是 AI Persona，并非现实中的本人。'
          : '建立一段长期对话，消息会安全保存在你的账号中。'}
      </Text>
      {onCreate ? (
        <View style={styles.action}>
          <AppButton onPress={onCreate} title="创建第一个 Persona" />
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: 'center', justifyContent: 'center', padding: spacing.x8 },
  title: {
    color: colors.text,
    fontSize: typography.sectionTitle,
    fontWeight: '800',
    marginTop: spacing.x5,
    textAlign: 'center',
  },
  description: {
    color: colors.textSecondary,
    fontSize: typography.helper,
    lineHeight: 21,
    marginTop: spacing.x2,
    maxWidth: 300,
    textAlign: 'center',
  },
  action: { marginTop: spacing.x6, width: '100%' },
});

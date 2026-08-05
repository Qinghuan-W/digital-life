import { PropsWithChildren } from 'react';
import {
  Keyboard,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleProp,
  StyleSheet,
  View,
  ViewStyle,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors, layout } from '@/constants/theme';

type PageContainerProps = PropsWithChildren<{
  scroll?: boolean;
  keyboardAware?: boolean;
  contentStyle?: StyleProp<ViewStyle>;
}>;

export function PageContainer({
  children,
  scroll = false,
  keyboardAware = false,
  contentStyle,
}: PageContainerProps) {
  const content = scroll ? (
    <ScrollView
      contentContainerStyle={styles.scrollContent}
      keyboardDismissMode={Platform.OS === 'ios' ? 'interactive' : 'on-drag'}
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}>
      <Pressable onPress={Keyboard.dismiss} style={[styles.content, contentStyle]}>
        {children}
      </Pressable>
    </ScrollView>
  ) : (
    <View style={[styles.content, contentStyle]}>{children}</View>
  );

  return (
    <SafeAreaView edges={['top', 'right', 'bottom', 'left']} style={styles.safeArea}>
      {keyboardAware ? (
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={styles.keyboardView}>
          {content}
        </KeyboardAvoidingView>
      ) : (
        content
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    backgroundColor: colors.background,
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
  },
  content: {
    alignSelf: 'center',
    flex: 1,
    maxWidth: layout.maxContentWidth,
    width: '100%',
  },
});

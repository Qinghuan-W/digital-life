import { useRef, useState } from 'react';
import {
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { AppButton } from '@/components/ui/AppButton';
import { AppInput } from '@/components/ui/AppInput';
import { FormError } from '@/components/ui/FormError';
import { colors, layout, spacing, typography } from '@/constants/theme';
import { updatePersona } from '@/features/personas/persona-service';
import { PersonaFieldErrors } from '@/features/personas/persona-types';
import { getUserFacingError } from '@/services/api-errors';
import { Persona } from '@/types/persona';

type EditPersonaSheetProps = {
  persona: Persona;
  visible: boolean;
  onClose: () => void;
  onUpdated: (persona: Persona) => void;
};

export function EditPersonaSheet({ persona, visible, onClose, onUpdated }: EditPersonaSheetProps) {
  const submissionLock = useRef(false);
  const [displayName, setDisplayName] = useState(persona.displayName);
  const [relationship, setRelationship] = useState(persona.relationshipLabel);
  const [age, setAge] = useState(persona.age?.toString() ?? '');
  const [gender, setGender] = useState(persona.genderLabel ?? '');
  const [description, setDescription] = useState(persona.description ?? '');
  const [errors, setErrors] = useState<PersonaFieldErrors>({});
  const [requestError, setRequestError] = useState<string>();
  const [submitting, setSubmitting] = useState(false);

  const requestClose = () => {
    if (!submitting) {
      onClose();
    }
  };

  const submit = async () => {
    if (submissionLock.current) {
      return;
    }
    const nextErrors: PersonaFieldErrors = {};
    const normalizedName = displayName.trim();
    const normalizedRelationship = relationship.trim();
    const normalizedGender = gender.trim();
    const normalizedDescription = description.trim();
    let parsedAge: number | null = null;

    if (!normalizedName) {
      nextErrors.displayName = '请输入 Persona 名字';
    } else if (normalizedName.length > 80) {
      nextErrors.displayName = '名字不能超过 80 个字符';
    }
    if (!normalizedRelationship) {
      nextErrors.relationshipLabel = '请输入与你的关系';
    } else if (normalizedRelationship.length > 50) {
      nextErrors.relationshipLabel = '关系不能超过 50 个字符';
    }
    if (age.trim()) {
      parsedAge = Number(age.trim());
      if (!/^\d+$/.test(age.trim()) || parsedAge < 1 || parsedAge > 150) {
        nextErrors.age = '年龄需要填写 1–150 之间的整数';
      }
    }
    if (normalizedGender.length > 50) {
      nextErrors.genderLabel = '性别不能超过 50 个字符';
    }
    if (normalizedDescription.length > 500) {
      nextErrors.description = '描述不能超过 500 个字符';
    }

    setErrors(nextErrors);
    setRequestError(undefined);
    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    submissionLock.current = true;
    setSubmitting(true);
    try {
      const updated = await updatePersona(persona.id, {
        displayName: normalizedName,
        relationshipLabel: normalizedRelationship,
        age: parsedAge,
        genderLabel:
          !normalizedGender || normalizedGender === '不指定' ? null : normalizedGender,
        description: normalizedDescription || null,
      });
      onUpdated(updated);
      onClose();
    } catch (error) {
      setRequestError(getUserFacingError(error));
    } finally {
      submissionLock.current = false;
      setSubmitting(false);
    }
  };

  return (
    <Modal
      animationType="slide"
      onRequestClose={requestClose}
      statusBarTranslucent
      transparent
      visible={visible}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.overlay}>
        <Pressable accessibilityLabel="关闭编辑弹窗" onPress={requestClose} style={styles.backdrop} />
        <View style={styles.sheet}>
          <View style={styles.handle} />
          <View style={styles.header}>
            <View>
              <Text style={styles.title}>Persona 资料</Text>
              <Text style={styles.subtitle}>修改后会从下一条回复开始生效。</Text>
            </View>
            <Pressable
              accessibilityLabel="关闭"
              accessibilityRole="button"
              disabled={submitting}
              hitSlop={10}
              onPress={requestClose}
              style={({ pressed }) => [styles.closeButton, pressed && styles.pressed]}>
              <Text style={styles.closeText}>×</Text>
            </Pressable>
          </View>

          <ScrollView
            contentContainerStyle={styles.form}
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}>
            <FormError message={requestError} />
            <AppInput
              error={errors.displayName}
              label="名字 *"
              maxLength={80}
              onChangeText={(value) => {
                setDisplayName(value);
                setErrors((current) => ({ ...current, displayName: undefined }));
              }}
              value={displayName}
            />
            <AppInput
              error={errors.relationshipLabel}
              label="与我的关系 *"
              maxLength={50}
              onChangeText={(value) => {
                setRelationship(value);
                setErrors((current) => ({ ...current, relationshipLabel: undefined }));
              }}
              value={relationship}
            />
            <AppInput
              error={errors.age}
              keyboardType="number-pad"
              label="年龄"
              maxLength={3}
              onChangeText={(value) => {
                setAge(value.replace(/[^0-9]/g, ''));
                setErrors((current) => ({ ...current, age: undefined }));
              }}
              placeholder="可选，1–150"
              value={age}
            />
            <AppInput
              error={errors.genderLabel}
              label="性别"
              maxLength={50}
              onChangeText={(value) => {
                setGender(value);
                setErrors((current) => ({ ...current, genderLabel: undefined }));
              }}
              placeholder="可选"
              value={gender}
            />
            <AppInput
              error={errors.description}
              label="简单描述"
              maxLength={500}
              multiline
              onChangeText={(value) => {
                setDescription(value);
                setErrors((current) => ({ ...current, description: undefined }));
              }}
              style={styles.descriptionInput}
              textAlignVertical="top"
              value={description}
            />
            <Text style={styles.characterCount}>{description.length}/500</Text>
          </ScrollView>

          <View style={styles.footer}>
            <AppButton
              loading={submitting}
              loadingTitle="正在保存……"
              onPress={submit}
              title="保存资料"
            />
          </View>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: { flex: 1, justifyContent: 'flex-end' },
  backdrop: {
    backgroundColor: 'rgba(11, 24, 18, 0.42)',
    bottom: 0,
    left: 0,
    position: 'absolute',
    right: 0,
    top: 0,
  },
  sheet: {
    alignSelf: 'center',
    backgroundColor: colors.surface,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '90%',
    maxWidth: layout.maxContentWidth,
    paddingTop: spacing.x2,
    width: '100%',
  },
  handle: {
    alignSelf: 'center',
    backgroundColor: colors.border,
    borderRadius: 3,
    height: 5,
    width: 44,
  },
  header: {
    alignItems: 'flex-start',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: layout.pagePadding,
    paddingVertical: spacing.x4,
  },
  title: { color: colors.text, fontSize: 22, fontWeight: '800' },
  subtitle: { color: colors.textSecondary, fontSize: typography.helper, marginTop: spacing.x1 },
  closeButton: { alignItems: 'center', height: 40, justifyContent: 'center', width: 40 },
  closeText: { color: colors.textSecondary, fontSize: 30, lineHeight: 32 },
  form: { gap: spacing.x4, paddingBottom: spacing.x5, paddingHorizontal: layout.pagePadding },
  descriptionInput: { minHeight: 96, paddingTop: spacing.x3 },
  characterCount: {
    color: colors.placeholder,
    fontSize: typography.caption,
    marginTop: -spacing.x3,
    textAlign: 'right',
  },
  footer: {
    borderTopColor: colors.border,
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingBottom: spacing.x5,
    paddingHorizontal: layout.pagePadding,
    paddingTop: spacing.x3,
  },
  pressed: { opacity: 0.62 },
});

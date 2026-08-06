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
import { colors, layout, radii, spacing, typography } from '@/constants/theme';
import { createPersona } from '@/features/personas/persona-service';
import { PersonaFieldErrors } from '@/features/personas/persona-types';
import { getUserFacingError } from '@/services/api-errors';
import { PersonaCreationResult } from '@/types/conversation';

const RELATIONSHIPS = ['朋友', '伴侣', '家人', '同学', '同事', '其他'] as const;
const GENDERS = ['女', '男', '非二元', '不指定', '其他'] as const;

type CreatePersonaSheetProps = {
  visible: boolean;
  onClose: () => void;
  onCreated: (result: PersonaCreationResult) => void;
};

export function CreatePersonaSheet({ visible, onClose, onCreated }: CreatePersonaSheetProps) {
  const submissionLock = useRef(false);
  const [displayName, setDisplayName] = useState('');
  const [relationship, setRelationship] = useState<string>('');
  const [customRelationship, setCustomRelationship] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState<string>('');
  const [customGender, setCustomGender] = useState('');
  const [description, setDescription] = useState('');
  const [errors, setErrors] = useState<PersonaFieldErrors>({});
  const [requestError, setRequestError] = useState<string>();
  const [submitting, setSubmitting] = useState(false);

  const resetForm = () => {
    setDisplayName('');
    setRelationship('');
    setCustomRelationship('');
    setAge('');
    setGender('');
    setCustomGender('');
    setDescription('');
    setErrors({});
    setRequestError(undefined);
  };

  const requestClose = () => {
    if (!submitting) {
      resetForm();
      onClose();
    }
  };

  const submit = async () => {
    if (submissionLock.current) {
      return;
    }

    const nextErrors: PersonaFieldErrors = {};
    const normalizedName = displayName.trim();
    const normalizedRelationship =
      relationship === '其他' ? customRelationship.trim() : relationship.trim();
    const normalizedGender = gender === '其他' ? customGender.trim() : gender.trim();
    const normalizedDescription = description.trim();
    let parsedAge: number | null = null;

    if (!normalizedName) {
      nextErrors.displayName = '请输入 Persona 名字';
    } else if (normalizedName.length > 80) {
      nextErrors.displayName = '名字不能超过 80 个字符';
    }
    if (!normalizedRelationship) {
      nextErrors.relationshipLabel = '请选择或填写与你的关系';
    } else if (normalizedRelationship.length > 50) {
      nextErrors.relationshipLabel = '关系不能超过 50 个字符';
    }
    if (age.trim()) {
      if (!/^\d+$/.test(age.trim())) {
        nextErrors.age = '年龄需要填写整数';
      } else {
        parsedAge = Number(age.trim());
        if (parsedAge < 1 || parsedAge > 150) {
          nextErrors.age = '年龄需要在 1–150 之间';
        }
      }
    }
    if (gender === '其他' && !normalizedGender) {
      nextErrors.genderLabel = '请填写性别';
    } else if (normalizedGender.length > 50) {
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
      const result = await createPersona({
        displayName: normalizedName,
        relationshipLabel: normalizedRelationship,
        age: parsedAge,
        genderLabel:
          !normalizedGender || normalizedGender === '不指定' ? null : normalizedGender,
        description: normalizedDescription || null,
      });
      onCreated(result);
      resetForm();
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
        <Pressable accessibilityLabel="关闭创建弹窗" onPress={requestClose} style={styles.backdrop} />
        <View style={styles.sheet}>
          <View style={styles.handle} />
          <View style={styles.header}>
            <View>
              <Text style={styles.title}>创建 Persona</Text>
              <Text style={styles.subtitle}>先保存基础资料，之后可以继续完善。</Text>
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
              autoCapitalize="words"
              error={errors.displayName}
              label="名字 *"
              maxLength={80}
              onChangeText={(value) => {
                setDisplayName(value);
                setErrors((current) => ({ ...current, displayName: undefined }));
              }}
              placeholder="例如：小雨"
              value={displayName}
            />

            <ChoiceField
              label="与我的关系 *"
              onSelect={(value) => {
                setRelationship(value);
                setErrors((current) => ({ ...current, relationshipLabel: undefined }));
              }}
              options={RELATIONSHIPS}
              selected={relationship}
            />
            {relationship === '其他' ? (
              <AppInput
                error={errors.relationshipLabel}
                label="自定义关系"
                maxLength={50}
                onChangeText={(value) => {
                  setCustomRelationship(value);
                  setErrors((current) => ({ ...current, relationshipLabel: undefined }));
                }}
                placeholder="输入你们的关系"
                value={customRelationship}
              />
            ) : errors.relationshipLabel ? (
              <Text style={styles.errorText}>{errors.relationshipLabel}</Text>
            ) : null}

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

            <ChoiceField
              label="性别"
              onSelect={(value) => {
                setGender(value);
                setErrors((current) => ({ ...current, genderLabel: undefined }));
              }}
              options={GENDERS}
              selected={gender}
            />
            {gender === '其他' ? (
              <AppInput
                error={errors.genderLabel}
                label="自定义性别"
                maxLength={50}
                onChangeText={(value) => {
                  setCustomGender(value);
                  setErrors((current) => ({ ...current, genderLabel: undefined }));
                }}
                placeholder="输入性别"
                value={customGender}
              />
            ) : null}

            <AppInput
              error={errors.description}
              label="简单描述"
              maxLength={500}
              multiline
              onChangeText={(value) => {
                setDescription(value);
                setErrors((current) => ({ ...current, description: undefined }));
              }}
              placeholder="例如：大学时期认识的朋友"
              style={styles.descriptionInput}
              textAlignVertical="top"
              value={description}
            />
            <Text style={styles.characterCount}>{description.length}/500</Text>
          </ScrollView>

          <View style={styles.footer}>
            <Text style={styles.disclaimer}>
              该角色是根据你提供的信息创建的 AI Persona，并非现实中的本人，其回复不代表现实人物当前的真实想法。
            </Text>
            <AppButton
              loading={submitting}
              loadingTitle="正在创建……"
              onPress={submit}
              title="创建并开始聊天"
            />
          </View>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

type ChoiceFieldProps<T extends string> = {
  label: string;
  options: readonly T[];
  selected: string;
  onSelect: (value: T) => void;
};

function ChoiceField<T extends string>({ label, options, selected, onSelect }: ChoiceFieldProps<T>) {
  return (
    <View style={styles.choiceField}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={styles.chips}>
        {options.map((option) => {
          const active = option === selected;
          return (
            <Pressable
              accessibilityRole="button"
              accessibilityState={{ selected: active }}
              key={option}
              onPress={() => onSelect(option)}
              style={({ pressed }) => [
                styles.chip,
                active && styles.chipActive,
                pressed && styles.pressed,
              ]}>
              <Text style={[styles.chipText, active && styles.chipTextActive]}>{option}</Text>
            </Pressable>
          );
        })}
      </View>
    </View>
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
    maxHeight: '92%',
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
  form: { gap: spacing.x4, paddingHorizontal: layout.pagePadding, paddingBottom: spacing.x5 },
  choiceField: { gap: spacing.x2 },
  fieldLabel: { color: colors.text, fontSize: typography.helper, fontWeight: '600' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.x2 },
  chip: {
    backgroundColor: colors.input,
    borderColor: 'transparent',
    borderRadius: radii.round,
    borderWidth: 1,
    minHeight: 38,
    paddingHorizontal: spacing.x4,
    justifyContent: 'center',
  },
  chipActive: { backgroundColor: colors.brandSoft, borderColor: colors.brand },
  chipText: { color: colors.textSecondary, fontSize: typography.helper },
  chipTextActive: { color: colors.brand, fontWeight: '700' },
  errorText: { color: colors.error, fontSize: typography.caption },
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
    gap: spacing.x3,
    paddingBottom: spacing.x5,
    paddingHorizontal: layout.pagePadding,
    paddingTop: spacing.x3,
  },
  disclaimer: { color: colors.textSecondary, fontSize: 12, lineHeight: 18 },
  pressed: { opacity: 0.62 },
});

import { CreatePersonaInput } from '@/types/persona';

export type PersonaFieldErrors = Partial<
  Record<'displayName' | 'relationshipLabel' | 'age' | 'genderLabel' | 'description', string>
>;

export type PersonaFormValues = Omit<CreatePersonaInput, 'age'> & {
  age: string;
};

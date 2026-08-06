export type Persona = {
  id: string;
  displayName: string;
  relationshipLabel: string;
  age: number | null;
  genderLabel: string | null;
  description: string | null;
  avatarUrl: string | null;
  createdAt: string;
  updatedAt: string;
};

export type PersonaSummary = Pick<
  Persona,
  'id' | 'displayName' | 'relationshipLabel' | 'age' | 'genderLabel'
>;

export type CreatePersonaInput = {
  displayName: string;
  relationshipLabel: string;
  age: number | null;
  genderLabel: string | null;
  description: string | null;
};

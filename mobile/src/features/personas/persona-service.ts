import { mapApiPersona, mapPersonaCreationResponse } from './persona-mappers';

import { apiRequest } from '@/services/api-client';
import { ApiPersona, ApiPersonaCreateResponse } from '@/types/api';
import { PersonaCreationResult } from '@/types/conversation';
import { CreatePersonaInput, Persona, UpdatePersonaInput } from '@/types/persona';

export async function createPersona(input: CreatePersonaInput): Promise<PersonaCreationResult> {
  const dto = await apiRequest<ApiPersonaCreateResponse>('/personas', {
    method: 'POST',
    authenticated: true,
    body: {
      display_name: input.displayName.trim(),
      relationship_label: input.relationshipLabel.trim(),
      age: input.age,
      gender_label: input.genderLabel?.trim() || null,
      description: input.description?.trim() || null,
    },
  });
  return mapPersonaCreationResponse(dto);
}

export async function getPersonas(): Promise<Persona[]> {
  const dto = await apiRequest<ApiPersona[]>('/personas', { authenticated: true });
  return dto.map(mapApiPersona);
}

export async function updatePersona(
  personaId: string,
  input: UpdatePersonaInput,
): Promise<Persona> {
  const dto = await apiRequest<ApiPersona>(`/personas/${personaId}`, {
    method: 'PATCH',
    authenticated: true,
    body: {
      display_name: input.displayName.trim(),
      relationship_label: input.relationshipLabel.trim(),
      age: input.age,
      gender_label: input.genderLabel?.trim() || null,
      description: input.description?.trim() || null,
    },
  });
  return mapApiPersona(dto);
}

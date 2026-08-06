import { ApiPersona, ApiPersonaCreateResponse, ApiPersonaSummary } from '@/types/api';
import { Conversation, PersonaCreationResult } from '@/types/conversation';
import { Persona, PersonaSummary } from '@/types/persona';

export function mapApiPersona(dto: ApiPersona): Persona {
  return {
    id: dto.id,
    displayName: dto.display_name,
    relationshipLabel: dto.relationship_label,
    age: dto.age,
    genderLabel: dto.gender_label,
    description: dto.description,
    avatarUrl: dto.avatar_url,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
  };
}

export function mapApiPersonaSummary(dto: ApiPersonaSummary): PersonaSummary {
  return {
    id: dto.id,
    displayName: dto.display_name,
    relationshipLabel: dto.relationship_label,
    age: dto.age,
    genderLabel: dto.gender_label,
  };
}

export function mapPersonaCreationResponse(dto: ApiPersonaCreateResponse): PersonaCreationResult {
  const persona = mapApiPersona(dto.persona);
  const conversation: Conversation = {
    id: dto.conversation.id,
    title: dto.conversation.title,
    persona: {
      id: persona.id,
      displayName: persona.displayName,
      relationshipLabel: persona.relationshipLabel,
      age: persona.age,
      genderLabel: persona.genderLabel,
    },
    lastMessagePreview: dto.conversation.last_message_preview,
    lastMessageRole: null,
    lastMessageAt: dto.conversation.last_message_at,
    createdAt: dto.conversation.created_at,
    updatedAt: dto.conversation.updated_at,
  };
  return { persona, conversation };
}

import { Persona, PersonaSummary } from './persona';

export type Conversation = {
  id: string;
  title: string;
  persona: PersonaSummary;
  lastMessagePreview: string | null;
  lastMessageRole: 'user' | 'assistant' | null;
  lastMessageAt: string | null;
  createdAt: string;
  updatedAt: string;
};

export type ConversationDetail = {
  id: string;
  title: string;
  persona: Persona;
  lastMessageAt: string | null;
  createdAt: string;
  updatedAt: string;
};

export type PersonaCreationResult = {
  persona: Persona;
  conversation: Conversation;
};

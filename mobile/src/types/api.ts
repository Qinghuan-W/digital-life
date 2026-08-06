export type ApiUser = {
  id: string;
  email: string;
  display_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type RegisterRequest = {
  email: string;
  display_name: string;
  password: string;
};

export type LoginRequest = {
  email: string;
  password: string;
};

export type AuthResponseDto = RefreshResponseDto & {
  user: ApiUser;
};

export type RefreshResponseDto = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
};

export type ApiErrorResponse = {
  error: string;
  message: string;
};

export type ApiPersona = {
  id: string;
  display_name: string;
  relationship_label: string;
  age: number | null;
  gender_label: string | null;
  description: string | null;
  avatar_url: string | null;
  created_at: string;
  updated_at: string;
};

export type ApiPersonaSummary = Pick<
  ApiPersona,
  'id' | 'display_name' | 'relationship_label' | 'age' | 'gender_label'
>;

export type ApiDefaultConversation = {
  id: string;
  persona_id: string;
  title: string;
  last_message_preview: string | null;
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ApiPersonaCreateResponse = {
  persona: ApiPersona;
  conversation: ApiDefaultConversation;
};

export type ApiConversationListItem = {
  id: string;
  title: string;
  persona: ApiPersonaSummary;
  last_message_preview: string | null;
  last_message_role: 'user' | 'assistant' | null;
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ApiConversationDetail = {
  id: string;
  title: string;
  persona: ApiPersona;
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ApiMessage = {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  status: 'completed' | 'failed';
  client_message_id: string | null;
  created_at: string;
  updated_at: string;
};

export type ApiMessageSendResponse = {
  user_message: ApiMessage;
  assistant_message: ApiMessage;
};

import {
  mapApiConversation,
  mapApiConversationDetail,
  mapApiMessage,
  mapMessageSendResponse,
} from './conversation-mappers';

import { apiRequest } from '@/services/api-client';
import {
  ApiConversationDetail,
  ApiConversationListItem,
  ApiMessage,
  ApiMessageSendResponse,
} from '@/types/api';
import { Conversation, ConversationDetail } from '@/types/conversation';
import { Message, MessageSendResult } from '@/types/message';

export async function getConversations(): Promise<Conversation[]> {
  const dto = await apiRequest<ApiConversationListItem[]>('/conversations', {
    authenticated: true,
  });
  return dto.map(mapApiConversation);
}

export async function getConversation(conversationId: string): Promise<ConversationDetail> {
  const dto = await apiRequest<ApiConversationDetail>(`/conversations/${conversationId}`, {
    authenticated: true,
  });
  return mapApiConversationDetail(dto);
}

export async function getMessages(
  conversationId: string,
  options: { limit?: number; before?: string } = {},
): Promise<Message[]> {
  const query = new URLSearchParams();
  query.set('limit', String(options.limit ?? 50));
  if (options.before) {
    query.set('before', options.before);
  }
  const dto = await apiRequest<ApiMessage[]>(
    `/conversations/${conversationId}/messages?${query.toString()}`,
    { authenticated: true },
  );
  return dto.map(mapApiMessage);
}

export async function sendMessage(
  conversationId: string,
  content: string,
  clientMessageId: string,
): Promise<MessageSendResult> {
  const dto = await apiRequest<ApiMessageSendResponse>(
    `/conversations/${conversationId}/messages`,
    {
      method: 'POST',
      authenticated: true,
      timeoutMs: 40_000,
      body: {
        content: content.trim(),
        client_message_id: clientMessageId,
      },
    },
  );
  return mapMessageSendResponse(dto);
}

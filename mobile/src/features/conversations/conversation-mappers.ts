import { mapApiPersona, mapApiPersonaSummary } from '@/features/personas/persona-mappers';
import {
  ApiConversationDetail,
  ApiConversationListItem,
  ApiMessage,
  ApiMessageSendResponse,
} from '@/types/api';
import { Conversation, ConversationDetail } from '@/types/conversation';
import { Message, MessageSendResult } from '@/types/message';

export function mapApiConversation(dto: ApiConversationListItem): Conversation {
  return {
    id: dto.id,
    title: dto.title,
    persona: mapApiPersonaSummary(dto.persona),
    lastMessagePreview: dto.last_message_preview,
    lastMessageRole: dto.last_message_role,
    lastMessageAt: dto.last_message_at,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
  };
}

export function mapApiConversationDetail(dto: ApiConversationDetail): ConversationDetail {
  return {
    id: dto.id,
    title: dto.title,
    persona: mapApiPersona(dto.persona),
    lastMessageAt: dto.last_message_at,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
  };
}

export function mapApiMessage(dto: ApiMessage): Message {
  return {
    id: dto.id,
    conversationId: dto.conversation_id,
    role: dto.role,
    content: dto.content,
    status: dto.status,
    clientMessageId: dto.client_message_id,
    replyToMessageId: dto.reply_to_message_id,
    sequenceIndex: dto.sequence_index,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
  };
}

export function mapMessageSendResponse(dto: ApiMessageSendResponse): MessageSendResult {
  const assistantMessages = dto.assistant_messages
    .map(mapApiMessage)
    .sort((left, right) => (left.sequenceIndex ?? 0) - (right.sequenceIndex ?? 0));
  return {
    userMessage: mapApiMessage(dto.user_message),
    assistantMessages,
    deliveryPlan: dto.delivery_plan.map((item) => ({
      messageId: item.message_id,
      delayMs: item.delay_ms,
    })),
  };
}

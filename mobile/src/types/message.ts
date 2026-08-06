export type MessageRole = 'user' | 'assistant';
export type MessageStatus = 'completed' | 'failed';
export type MessageDeliveryState = 'sending' | 'failed';

export type Message = {
  id: string;
  conversationId: string;
  role: MessageRole;
  content: string;
  status: MessageStatus;
  clientMessageId: string | null;
  createdAt: string;
  updatedAt: string;
  deliveryState?: MessageDeliveryState;
};

export type MessageSendResult = {
  userMessage: Message;
  assistantMessage: Message;
};

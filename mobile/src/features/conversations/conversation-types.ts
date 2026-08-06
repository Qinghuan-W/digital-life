import { Message } from '@/types/message';

export type ConversationLoadState = 'loading' | 'ready' | 'error';

export type PendingMessage = Message & {
  clientMessageId: string;
  role: 'user';
};

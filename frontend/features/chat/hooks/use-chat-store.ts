import { create } from "zustand";
import type { ChatMessage } from "@/features/chat/types/chat";

interface ChatState {
  messagesByConversation: Record<number, ChatMessage[]>;
  setMessages: (conversationId: number, messages: ChatMessage[]) => void;
  appendMessage: (conversationId: number, message: ChatMessage) => void;
  updateMessage: (conversationId: number, messageId: string, patch: Partial<ChatMessage>) => void;
  clearConversation: (conversationId: number) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messagesByConversation: {},
  setMessages: (conversationId, messages) =>
    set((state) => ({
      messagesByConversation: { ...state.messagesByConversation, [conversationId]: messages },
    })),
  appendMessage: (conversationId, message) =>
    set((state) => ({
      messagesByConversation: {
        ...state.messagesByConversation,
        [conversationId]: [...(state.messagesByConversation[conversationId] ?? []), message],
      },
    })),
  updateMessage: (conversationId, messageId, patch) =>
    set((state) => ({
      messagesByConversation: {
        ...state.messagesByConversation,
        [conversationId]: (state.messagesByConversation[conversationId] ?? []).map((message) =>
          message.id === messageId ? { ...message, ...patch } : message,
        ),
      },
    })),
  clearConversation: (conversationId) =>
    set((state) => {
      const next = { ...state.messagesByConversation };
      delete next[conversationId];
      return { messagesByConversation: next };
    }),
}));

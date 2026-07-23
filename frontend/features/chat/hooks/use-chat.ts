import { useCallback, useEffect, useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  chatKeys,
  getChatHistory,
  sendChatMessage,
  resumeChat,
} from "@/features/chat/api/chat-api";
import { useChatStore } from "@/features/chat/hooks/use-chat-store";
import type { ChatMessage } from "@/features/chat/types/chat";
import { toApiFailure } from "@/services/api";

function createMessage(
  conversationId: number,
  role: ChatMessage["role"],
  content: string,
): ChatMessage {
  return {
    id: crypto.randomUUID(),
    conversationId,
    role,
    content,
    createdAt: new Date().toISOString(),
  };
}

async function revealResponse(
  conversationId: number,
  messageId: string,
  content: string,
  updateMessage: (conversationId: number, messageId: string, patch: Partial<ChatMessage>) => void,
) {
  const chunkSize = Math.max(4, Math.ceil(content.length / 48));
  updateMessage(conversationId, messageId, { content: "", pending: false, streaming: true });

  for (let offset = chunkSize; offset < content.length; offset += chunkSize) {
    updateMessage(conversationId, messageId, { content: content.slice(0, offset) });
    await new Promise((resolve) => setTimeout(resolve, 12));
  }

  updateMessage(conversationId, messageId, { content, streaming: false });
}

export function useChat(conversationId: number | null) {
  const queryClient = useQueryClient();
  const messagesByConversation = useChatStore((state) => state.messagesByConversation);
  const setMessages = useChatStore((state) => state.setMessages);
  const appendMessage = useChatStore((state) => state.appendMessage);
  const updateMessage = useChatStore((state) => state.updateMessage);
  const messages = useMemo(
    () => (conversationId ? (messagesByConversation[conversationId] ?? []) : []),
    [conversationId, messagesByConversation],
  );
  const historyQuery = useQuery({
    queryKey: conversationId ? chatKeys.history(conversationId) : ["chat", "history", "empty"],
    queryFn: () => getChatHistory(Number(conversationId)),
    enabled: Boolean(conversationId),
  });

  useEffect(() => {
    if (!conversationId || !historyQuery.data) return;
    setMessages(
      conversationId,
      historyQuery.data.map((message) => ({
        id: String(message.id),
        conversationId: message.conversation_id,
        role: message.role,
        content: message.content,
        createdAt: message.created_at,
      })),
    );
  }, [conversationId, historyQuery.data, setMessages]);

  const chatMutation = useMutation({
    mutationFn: ({ id, message }: { id: number; message: string }) => sendChatMessage(id, message),
  });

  const resumeMutation = useMutation({
    mutationFn: ({
      id,
      decision,
      message,
    }: {
      id: number;
      decision: "approve" | "reject";
      message?: string;
    }) => resumeChat(id, decision, message),
  });

  const sendMessage = useCallback(
    async (content: string) => {
      if (!conversationId) return;
      const trimmed = content.trim();
      if (!trimmed) return;

      appendMessage(conversationId, createMessage(conversationId, "user", trimmed));
      const pendingAssistant = { ...createMessage(conversationId, "assistant", ""), pending: true };
      appendMessage(conversationId, pendingAssistant);

      try {
        const response = await chatMutation.mutateAsync({ id: conversationId, message: trimmed });
        await revealResponse(
          conversationId,
          pendingAssistant.id,
          response.response ?? "The assistant requires a decision before continuing.",
          updateMessage,
        );
        updateMessage(conversationId, pendingAssistant.id, { interrupt: response.interrupt });
        await queryClient.invalidateQueries({ queryKey: chatKeys.history(conversationId) });
      } catch (error) {
        const failure = toApiFailure(error);
        updateMessage(conversationId, pendingAssistant.id, {
          content: "",
          pending: false,
          error: failure.message,
        });
      }
    },
    [appendMessage, chatMutation, conversationId, queryClient, updateMessage],
  );

  const continueResponse = useCallback(
    async (decision: "approve" | "reject" = "approve") => {
      if (!conversationId) return;
      const pendingAssistant = { ...createMessage(conversationId, "assistant", ""), pending: true };
      appendMessage(conversationId, pendingAssistant);

      try {
        const response = await resumeMutation.mutateAsync({ id: conversationId, decision });
        await revealResponse(
          conversationId,
          pendingAssistant.id,
          response.response ?? "No additional response was returned.",
          updateMessage,
        );
        updateMessage(conversationId, pendingAssistant.id, { interrupt: response.interrupt });
        await queryClient.invalidateQueries({ queryKey: chatKeys.history(conversationId) });
      } catch (error) {
        updateMessage(conversationId, pendingAssistant.id, {
          pending: false,
          error: toApiFailure(error).message,
        });
      }
    },
    [appendMessage, conversationId, queryClient, resumeMutation, updateMessage],
  );

  return {
    messages,
    sendMessage,
    continueResponse,
    isSending: chatMutation.isPending || resumeMutation.isPending,
    isLoadingHistory: historyQuery.isLoading,
    historyError: historyQuery.error,
    retryHistory: historyQuery.refetch,
  };
}

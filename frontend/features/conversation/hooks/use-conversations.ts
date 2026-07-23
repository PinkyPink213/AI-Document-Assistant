import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  conversationKeys,
  createConversation,
  deleteConversation,
  getConversation,
  listConversations,
  updateConversation,
} from "@/features/conversation/api/conversation-api";
import type { Conversation } from "@/features/conversation/types/conversation";
import { useAppStore } from "@/store/use-app-store";
import { documentKeys } from "@/features/documents/api/document-api";
import { chatKeys } from "@/features/chat/api/chat-api";
import { useChatStore } from "@/features/chat/hooks/use-chat-store";

export function useConversations() {
  return useQuery({
    queryKey: conversationKeys.all,
    queryFn: listConversations,
  });
}

export function useConversation(conversationId: number | null) {
  return useQuery({
    queryKey: conversationId ? conversationKeys.detail(conversationId) : ["conversation", "empty"],
    queryFn: () => getConversation(Number(conversationId)),
    enabled: Boolean(conversationId),
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();
  const setCurrentConversationId = useAppStore((state) => state.setCurrentConversationId);

  return useMutation({
    mutationFn: createConversation,
    onSuccess: (conversation) => {
      queryClient.setQueryData<Conversation[]>(conversationKeys.all, (current = []) => [
        conversation,
        ...current,
      ]);
      setCurrentConversationId(conversation.id);
    },
  });
}

export function useUpdateConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, title }: { id: number; title: string }) => updateConversation(id, { title }),
    onMutate: async ({ id, title }) => {
      await queryClient.cancelQueries({ queryKey: conversationKeys.all });
      const previous = queryClient.getQueryData<Conversation[]>(conversationKeys.all);
      queryClient.setQueryData<Conversation[]>(conversationKeys.all, (current = []) =>
        current.map((conversation) =>
          conversation.id === id ? { ...conversation, title } : conversation,
        ),
      );
      return { previous };
    },
    onError: (_error, _variables, context) => {
      queryClient.setQueryData(conversationKeys.all, context?.previous);
    },
    onSettled: async (_data, _error, variables) => {
      await queryClient.invalidateQueries({ queryKey: conversationKeys.all });
      await queryClient.invalidateQueries({ queryKey: conversationKeys.detail(variables.id) });
    },
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();
  const currentConversationId = useAppStore((state) => state.currentConversationId);
  const setCurrentConversationId = useAppStore((state) => state.setCurrentConversationId);
  const clearChatConversation = useChatStore((state) => state.clearConversation);

  return useMutation({
    mutationFn: deleteConversation,
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: conversationKeys.all });
      const previous = queryClient.getQueryData<Conversation[]>(conversationKeys.all);
      queryClient.setQueryData<Conversation[]>(conversationKeys.all, (current = []) =>
        current.filter((conversation) => conversation.id !== id),
      );
      if (currentConversationId === id) setCurrentConversationId(null);
      return { previous, previousSelected: currentConversationId };
    },
    onError: (_error, _id, context) => {
      queryClient.setQueryData(conversationKeys.all, context?.previous);
      if (context?.previousSelected) {
        setCurrentConversationId(context.previousSelected);
      }
    },
    onSuccess: (_data, id) => {
      clearChatConversation(id);
      queryClient.removeQueries({ queryKey: conversationKeys.detail(id) });
      queryClient.removeQueries({ queryKey: documentKeys.byConversation(id) });
      queryClient.removeQueries({ queryKey: chatKeys.history(id) });
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: conversationKeys.all }),
  });
}

import { api } from "@/services/api";
import type {
  Conversation,
  ConversationCreateRequest,
  ConversationUpdateRequest,
} from "@/features/conversation/types/conversation";

export const conversationKeys = {
  all: ["conversations"] as const,
  detail: (conversationId: number) => ["conversations", conversationId] as const,
};

export async function listConversations() {
  const { data } = await api.get<Conversation[]>("/conversation");
  return data;
}

export async function createConversation(payload: ConversationCreateRequest) {
  const { data } = await api.post<Conversation>("/conversation", payload);
  return data;
}

export async function getConversation(conversationId: number) {
  const { data } = await api.get<Conversation>(`/conversation/${conversationId}`);
  return data;
}

export async function updateConversation(
  conversationId: number,
  payload: ConversationUpdateRequest,
) {
  const { data } = await api.put<Conversation>(`/conversation/${conversationId}`, payload);
  return data;
}

export async function deleteConversation(conversationId: number) {
  await api.delete<void>(`/conversation/${conversationId}`);
}

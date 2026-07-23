import { api } from "@/services/api";
import type {
  ChatHistoryMessage,
  ChatRequest,
  ChatResponse,
  ResumeRequest,
} from "@/features/chat/types/chat";

export const chatKeys = {
  history: (conversationId: number) => ["chat", "history", conversationId] as const,
};

export async function getChatHistory(conversationId: number) {
  const { data } = await api.get<ChatHistoryMessage[]>(`/conversations/${conversationId}/messages`);
  return data;
}

export async function sendChatMessage(conversationId: number, message: string) {
  const payload: ChatRequest = { conversation_id: conversationId, message };
  const { data } = await api.post<ChatResponse>(`/conversations/${conversationId}/chat`, payload, {
    timeout: 120_000,
  });
  return data;
}

export async function resumeChat(
  conversationId: number,
  decision: ResumeRequest["decision"],
  message?: string,
) {
  const payload: ResumeRequest = {
    conversation_id: conversationId,
    decision,
    message: message ?? null,
  };
  const { data } = await api.post<ChatResponse>(
    `/conversations/${conversationId}/chat/resume`,
    payload,
    { timeout: 120_000 },
  );
  return data;
}

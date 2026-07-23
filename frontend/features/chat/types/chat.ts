export type ChatRole = "user" | "assistant" | "system";

export interface ChatMessage {
  id: string;
  conversationId: number;
  role: ChatRole;
  content: string;
  createdAt: string;
  pending?: boolean;
  streaming?: boolean;
  interrupt?: Record<string, unknown> | null;
  error?: string;
}

export interface ChatRequest {
  conversation_id: number;
  message: string;
}

export interface ResumeRequest {
  conversation_id: number;
  decision: "approve" | "reject";
  message?: string | null;
}

export interface ChatResponse {
  response: string | null;
  interrupt: Record<string, unknown> | null;
}

export interface ChatHistoryMessage {
  id: number;
  conversation_id: number;
  role: ChatRole;
  content: string;
  created_at: string;
}

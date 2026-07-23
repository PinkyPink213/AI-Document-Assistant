export interface Conversation {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationCreateRequest {
  title: string;
}

export interface ConversationUpdateRequest {
  title: string;
}

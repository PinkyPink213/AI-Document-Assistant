export interface DocumentResource {
  id: number;
  conversation_id: number;
  filename: string;
  created_at: string;
  updated_at: string;
  chunk_count?: number;
}

export interface DeleteDocumentResponse {
  message: string;
}

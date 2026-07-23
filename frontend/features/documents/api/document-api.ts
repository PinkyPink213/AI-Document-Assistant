import { api } from "@/services/api";
import type { DeleteDocumentResponse, DocumentResource } from "@/features/documents/types/document";
import type { AxiosRequestConfig } from "axios";

export const documentKeys = {
  byConversation: (conversationId: number) => ["documents", conversationId] as const,
};

export async function listDocuments(conversationId: number) {
  const { data } = await api.get<DocumentResource[]>(`/${conversationId}/documents`);
  return data;
}

export async function uploadDocument(
  conversationId: number,
  file: File,
  onProgress?: (progress: number) => void,
) {
  const formData = new FormData();
  formData.append("file", file);
  const config: AxiosRequestConfig<FormData> = {
    headers: { "Content-Type": "multipart/form-data" },
  };

  if (onProgress) {
    config.onUploadProgress = (event) => {
      if (event.total) onProgress?.(Math.round((event.loaded / event.total) * 100));
    };
  }

  const { data } = await api.post<DocumentResource>(
    `/${conversationId}/documents`,
    formData,
    config,
  );
  return data;
}

export async function deleteDocument(documentId: number) {
  const { data } = await api.delete<DeleteDocumentResponse>(`/documents/${documentId}`);
  return data;
}

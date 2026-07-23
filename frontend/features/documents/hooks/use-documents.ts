import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  deleteDocument,
  documentKeys,
  listDocuments,
  uploadDocument,
} from "@/features/documents/api/document-api";

export function useDocuments(conversationId: number | null) {
  return useQuery({
    queryKey: conversationId ? documentKeys.byConversation(conversationId) : ["documents", "empty"],
    queryFn: () => listDocuments(Number(conversationId)),
    enabled: Boolean(conversationId),
  });
}

export function useUploadDocument(conversationId: number | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, onProgress }: { file: File; onProgress?: (progress: number) => void }) => {
      if (!conversationId) throw new Error("Select a conversation before uploading.");
      return uploadDocument(conversationId, file, onProgress);
    },
    onSuccess: async () => {
      if (conversationId) {
        await queryClient.invalidateQueries({
          queryKey: documentKeys.byConversation(conversationId),
        });
      }
    },
  });
}

export function useDeleteDocument(conversationId: number | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteDocument,
    onSuccess: async () => {
      if (conversationId) {
        await queryClient.invalidateQueries({
          queryKey: documentKeys.byConversation(conversationId),
        });
      }
    },
  });
}

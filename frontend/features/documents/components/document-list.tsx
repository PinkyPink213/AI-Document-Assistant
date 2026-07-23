"use client";

import { FileText, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { useDeleteDocument, useDocuments } from "@/features/documents/hooks/use-documents";
import { toApiFailure } from "@/services/api";

export function DocumentList({ conversationId }: { conversationId: number | null }) {
  const { toast } = useToast();
  const { data: documents = [], isLoading, refetch, error } = useDocuments(conversationId);
  const deleteMutation = useDeleteDocument(conversationId);

  async function handleDelete(documentId: number) {
    try {
      await deleteMutation.mutateAsync(documentId);
      toast({ title: "Document deleted", tone: "success" });
    } catch (caught) {
      toast({ title: "Delete failed", description: toApiFailure(caught).message, tone: "error" });
    }
  }

  if (!conversationId) {
    return (
      <p className="text-sm text-muted-foreground">
        Select a conversation to see uploaded documents.
      </p>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }, (_, index) => (
          <Skeleton key={index} className="h-12" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md border p-3 text-sm">
        <p className="text-muted-foreground">Documents could not load.</p>
        <Button className="mt-2" size="sm" variant="outline" onClick={() => void refetch()}>
          Retry
        </Button>
      </div>
    );
  }

  if (!documents.length) {
    return <p className="text-sm text-muted-foreground">No documents uploaded yet.</p>;
  }

  return (
    <div className="space-y-2">
      {documents.map((document) => (
        <div
          key={document.id}
          className="grid grid-cols-[auto_1fr_auto] items-center gap-2 rounded-md border bg-surface-raised p-2"
        >
          <FileText className="h-4 w-4 text-muted-foreground" aria-hidden />
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{document.filename}</p>
            <p className="text-xs text-muted-foreground">
              {document.chunk_count ? `${document.chunk_count} chunks` : "Indexed document"}
            </p>
          </div>
          <Button
            size="icon"
            variant="ghost"
            aria-label={`Delete ${document.filename}`}
            disabled={deleteMutation.isPending}
            onClick={() => void handleDelete(document.id)}
          >
            <Trash2 className="h-4 w-4" aria-hidden />
          </Button>
        </div>
      ))}
    </div>
  );
}

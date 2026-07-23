"use client";

import { useCallback, useState } from "react";
import { useDropzone, type FileRejection } from "react-dropzone";
import { FileUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { useUploadDocument } from "@/features/documents/hooks/use-documents";
import { useDocuments } from "@/features/documents/hooks/use-documents";
import { toApiFailure } from "@/services/api";
import { cn } from "@/utils/cn";

const MAX_FILE_SIZE = 20 * 1024 * 1024;

export function DocumentUploader({ conversationId }: { conversationId: number | null }) {
  const { toast } = useToast();
  const [progress, setProgress] = useState(0);
  const uploadMutation = useUploadDocument(conversationId);
  const { data: documents = [] } = useDocuments(conversationId);

  const onDrop = useCallback(
    async (acceptedFiles: File[], fileRejections: FileRejection[]) => {
      if (fileRejections.length) {
        const reason = fileRejections[0]?.errors[0]?.code;
        const message =
          reason === "file-too-large"
            ? "Upload PDFs up to 20MB."
            : reason === "file-invalid-type"
              ? "Only PDF files are supported."
              : "This file could not be uploaded.";
        toast({ title: "Invalid file", description: message, tone: "error" });
        return;
      }

      const file = acceptedFiles[0];
      if (!file) return;
      if (file.type !== "application/pdf") {
        toast({
          title: "Invalid file",
          description: "Only PDF files are supported.",
          tone: "error",
        });
        return;
      }
      if (file.size > MAX_FILE_SIZE) {
        toast({ title: "File too large", description: "Upload PDFs up to 20MB.", tone: "error" });
        return;
      }
      const duplicate = documents.some(
        (document) => document.filename.trim().toLowerCase() === file.name.trim().toLowerCase(),
      );
      if (duplicate) {
        toast({
          title: "Duplicate file",
          description: `${file.name} is already uploaded in this conversation.`,
          tone: "error",
        });
        return;
      }

      setProgress(0);
      try {
        await uploadMutation.mutateAsync({ file, onProgress: setProgress });
        toast({ title: "Document uploaded", description: file.name, tone: "success" });
      } catch (caught) {
        const failure = toApiFailure(caught);
        toast({
          title: failure.status === 409 ? "Duplicate file" : "Upload failed",
          description: failure.message,
          tone: "error",
        });
      } finally {
        setProgress(0);
      }
    },
    [documents, toast, uploadMutation],
  );

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    multiple: false,
    noClick: true,
    disabled: !conversationId || uploadMutation.isPending,
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        "rounded-lg border border-dashed bg-surface-raised p-4 text-center transition-colors",
        isDragActive && "border-primary bg-primary/5",
        !conversationId && "opacity-60",
      )}
    >
      <input {...getInputProps()} aria-label="Upload PDF document" />
      <FileUp className="mx-auto h-7 w-7 text-muted-foreground" aria-hidden />
      <p className="mt-2 text-sm font-medium">Drop PDF documents</p>
      <p className="mt-1 text-xs text-muted-foreground">20MB maximum per file</p>
      {conversationId ? (
        <p className="mt-1 text-xs text-muted-foreground">
          {documents.length} {documents.length === 1 ? "PDF" : "PDFs"} already uploaded
        </p>
      ) : null}
      {uploadMutation.isPending ? (
        <div
          className="mt-3 h-2 overflow-hidden rounded-full bg-muted"
          aria-label={`Upload ${progress}% complete`}
        >
          <div className="h-full bg-primary transition-all" style={{ width: `${progress}%` }} />
        </div>
      ) : (
        <Button
          className="mt-3"
          variant="outline"
          size="sm"
          disabled={!conversationId}
          onClick={open}
        >
          Browse PDF
        </Button>
      )}
    </div>
  );
}

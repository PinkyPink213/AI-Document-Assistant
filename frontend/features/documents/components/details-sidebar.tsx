"use client";

import { motion } from "framer-motion";
import { PanelRightClose } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DocumentList } from "@/features/documents/components/document-list";
import { DocumentUploader } from "@/features/documents/components/document-uploader";
import { useDocuments } from "@/features/documents/hooks/use-documents";
import { useConversation, useConversations } from "@/features/conversation/hooks/use-conversations";
import { HealthStatus } from "@/features/health/components/health-status";
import { useAppStore } from "@/store/use-app-store";

function formatDate(value?: string) {
  if (!value) return "Not available";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );
}

export function DetailsSidebar() {
  const conversationId = useAppStore((state) => state.currentConversationId);
  const setRightSidebarOpen = useAppStore((state) => state.setRightSidebarOpen);
  const { data: conversation } = useConversation(conversationId);
  const { data: conversations = [] } = useConversations();
  const { data: documents = [] } = useDocuments(conversationId);

  return (
    <motion.aside
      initial={{ x: 24, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className="flex h-full min-h-0 flex-col border-l bg-surface"
      aria-label="Conversation details"
    >
      <header className="flex h-14 items-center justify-between border-b px-4">
        <p className="text-sm font-semibold">Details</p>
        <Button
          size="icon"
          variant="ghost"
          aria-label="Close details panel"
          onClick={() => setRightSidebarOpen(false)}
        >
          <PanelRightClose className="h-4 w-4" aria-hidden />
        </Button>
      </header>
      <div className="scrollbar-thin min-h-0 flex-1 space-y-6 overflow-y-auto p-4">
        <section>
          <h2 className="text-sm font-semibold">Conversation</h2>
          <dl className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between gap-3">
              <dt className="text-muted-foreground">Title</dt>
              <dd className="truncate font-medium">{conversation?.title ?? "None selected"}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-muted-foreground">Updated</dt>
              <dd className="text-right">{formatDate(conversation?.updated_at)}</dd>
            </div>
          </dl>
        </section>

        <section>
          <h2 className="text-sm font-semibold">Upload</h2>
          <div className="mt-3">
            <DocumentUploader conversationId={conversationId} />
          </div>
        </section>

        <section>
          <h2 className="text-sm font-semibold">Documents</h2>
          <div className="mt-3">
            <DocumentList conversationId={conversationId} />
          </div>
        </section>

        <section>
          <h2 className="text-sm font-semibold">Health Status</h2>
          <div className="mt-3">
            <HealthStatus />
          </div>
        </section>

        <section>
          <h2 className="text-sm font-semibold">Statistics</h2>
          <div className="mt-3 grid grid-cols-2 gap-2">
            <div className="rounded-md border bg-surface-raised p-3">
              <p className="text-2xl font-semibold">{conversations.length}</p>
              <p className="text-xs text-muted-foreground">Conversations</p>
            </div>
            <div className="rounded-md border bg-surface-raised p-3">
              <p className="text-2xl font-semibold">{documents.length}</p>
              <p className="text-xs text-muted-foreground">Documents</p>
            </div>
          </div>
        </section>
      </div>
    </motion.aside>
  );
}

"use client";

import { useCallback, useState } from "react";
import { PanelRightOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChatComposer } from "@/features/chat/components/chat-composer";
import { MessageList } from "@/features/chat/components/message-list";
import { useChat } from "@/features/chat/hooks/use-chat";
import { useAppStore } from "@/store/use-app-store";

export function ChatPanel() {
  const conversationId = useAppStore((state) => state.currentConversationId);
  const rightSidebarOpen = useAppStore((state) => state.rightSidebarOpen);
  const setRightSidebarOpen = useAppStore((state) => state.setRightSidebarOpen);
  const { messages, sendMessage, continueResponse, isSending } = useChat(conversationId);
  const [draft, setDraft] = useState("");

  const handleSend = useCallback(() => {
    const message = draft;
    setDraft("");
    void sendMessage(message);
  }, [draft, sendMessage]);

  return (
    <section className="flex min-h-0 flex-1 flex-col bg-background" aria-label="Chat workspace">
      <header className="flex h-14 items-center justify-between border-b bg-surface px-4">
        <div>
          <p className="text-sm font-semibold">Document Assistant</p>
          <p className="text-xs text-muted-foreground">
            {conversationId ? `Conversation #${conversationId}` : "Select a conversation to begin"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={!conversationId || isSending}
            onClick={() => void continueResponse()}
          >
            Continue Response
          </Button>
          {!rightSidebarOpen ? (
            <Button
              size="icon"
              variant="ghost"
              aria-label="Open details panel"
              onClick={() => setRightSidebarOpen(true)}
            >
              <PanelRightOpen className="h-4 w-4" aria-hidden />
            </Button>
          ) : null}
        </div>
      </header>
      <div className="min-h-0 flex-1">
        <MessageList
          messages={messages}
          onRegenerate={() => void continueResponse()}
          onDecision={(decision) => void continueResponse(decision)}
        />
      </div>
      <ChatComposer
        value={draft}
        disabled={!conversationId || isSending}
        onChange={setDraft}
        onSend={handleSend}
      />
    </section>
  );
}

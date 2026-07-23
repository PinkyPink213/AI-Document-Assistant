"use client";

import { memo, useMemo, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import { Check, MessageSquarePlus, Pencil, Search, Trash2, X } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import {
  useConversations,
  useCreateConversation,
  useDeleteConversation,
  useUpdateConversation,
} from "@/features/conversation/hooks/use-conversations";
import type { Conversation } from "@/features/conversation/types/conversation";
import { toApiFailure } from "@/services/api";
import { useAppStore } from "@/store/use-app-store";
import { cn } from "@/utils/cn";

const conversationSchema = z.object({
  title: z
    .string()
    .min(3, "Use at least 3 characters.")
    .max(100, "Keep titles under 100 characters."),
});

type ConversationForm = z.infer<typeof conversationSchema>;

interface ConversationRowProps {
  conversation: Conversation;
  active: boolean;
  onSelect: (id: number) => void;
  onRename: (id: number, title: string) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
}

const ConversationRow = memo(function ConversationRow({
  conversation,
  active,
  onSelect,
  onRename,
  onDelete,
}: ConversationRowProps) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(conversation.title);

  if (editing) {
    return (
      <div className="rounded-md border bg-surface p-2">
        <Input
          value={title}
          aria-label="Conversation title"
          onChange={(event) => setTitle(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              void onRename(conversation.id, title).then(() => setEditing(false));
            }
            if (event.key === "Escape") setEditing(false);
          }}
          autoFocus
        />
        <div className="mt-2 flex justify-end gap-1">
          <Button
            size="icon"
            variant="ghost"
            aria-label="Cancel rename"
            onClick={() => setEditing(false)}
          >
            <X className="h-4 w-4" aria-hidden />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            aria-label="Save conversation title"
            onClick={() => void onRename(conversation.id, title).then(() => setEditing(false))}
          >
            <Check className="h-4 w-4" aria-hidden />
          </Button>
        </div>
      </div>
    );
  }

  return (
    <button
      type="button"
      className={cn(
        "group grid w-full grid-cols-[1fr_auto] items-center gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors hover:bg-muted",
        active && "bg-muted",
      )}
      onClick={() => onSelect(conversation.id)}
    >
      <span className="truncate font-medium">{conversation.title}</span>
      <span className="flex gap-1 opacity-0 transition-opacity group-hover:opacity-100 group-focus:opacity-100">
        <span
          role="button"
          tabIndex={0}
          aria-label="Rename conversation"
          className="rounded p-1 hover:bg-surface"
          onClick={(event) => {
            event.stopPropagation();
            setEditing(true);
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter") setEditing(true);
          }}
        >
          <Pencil className="h-3.5 w-3.5" aria-hidden />
        </span>
        <span
          role="button"
          tabIndex={0}
          aria-label="Delete conversation"
          className="rounded p-1 hover:bg-surface"
          onClick={(event) => {
            event.stopPropagation();
            void onDelete(conversation.id);
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter") void onDelete(conversation.id);
          }}
        >
          <Trash2 className="h-3.5 w-3.5" aria-hidden />
        </span>
      </span>
    </button>
  );
});

export function ConversationSidebar() {
  const { toast } = useToast();
  const [search, setSearch] = useState("");
  const currentConversationId = useAppStore((state) => state.currentConversationId);
  const setCurrentConversationId = useAppStore((state) => state.setCurrentConversationId);
  const { data: conversations = [], isLoading, refetch, error } = useConversations();
  const createMutation = useCreateConversation();
  const updateMutation = useUpdateConversation();
  const deleteMutation = useDeleteConversation();

  const form = useForm<ConversationForm>({
    resolver: zodResolver(conversationSchema),
    defaultValues: { title: "New research conversation" },
  });

  const filtered = useMemo(
    () =>
      conversations.filter((conversation) =>
        conversation.title.toLowerCase().includes(search.toLowerCase()),
      ),
    [conversations, search],
  );

  async function handleCreate(values: ConversationForm) {
    try {
      const conversation = await createMutation.mutateAsync(values);
      toast({ title: "Conversation created", description: conversation.title, tone: "success" });
      form.reset({ title: "New research conversation" });
    } catch (caught) {
      toast({
        title: "Could not create conversation",
        description: toApiFailure(caught).message,
        tone: "error",
      });
    }
  }

  async function handleRename(id: number, title: string) {
    try {
      await updateMutation.mutateAsync({ id, title });
      toast({ title: "Conversation renamed", tone: "success" });
    } catch (caught) {
      toast({ title: "Rename failed", description: toApiFailure(caught).message, tone: "error" });
    }
  }

  async function handleDelete(id: number) {
    try {
      await deleteMutation.mutateAsync(id);
      toast({ title: "Conversation deleted", tone: "success" });
    } catch (caught) {
      toast({ title: "Delete failed", description: toApiFailure(caught).message, tone: "error" });
    }
  }

  return (
    <motion.aside
      initial={{ x: -24, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className="flex h-full min-h-0 flex-col border-r bg-surface"
      aria-label="Conversation sidebar"
    >
      <div className="border-b p-3">
        <form className="grid gap-2" onSubmit={form.handleSubmit(handleCreate)}>
          <Input aria-label="New conversation title" {...form.register("title")} />
          {form.formState.errors.title ? (
            <p className="text-xs text-destructive">{form.formState.errors.title.message}</p>
          ) : null}
          <Button type="submit" disabled={createMutation.isPending}>
            <MessageSquarePlus className="h-4 w-4" aria-hidden />
            New Conversation
          </Button>
        </form>
      </div>

      <div className="border-b p-3">
        <div className="relative">
          <Search
            className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground"
            aria-hidden
          />
          <Input
            className="pl-8"
            placeholder="Search conversations"
            value={search}
            aria-label="Search conversations"
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
      </div>

      <div className="scrollbar-thin min-h-0 flex-1 space-y-1 overflow-y-auto p-2">
        {isLoading ? (
          Array.from({ length: 8 }, (_, index) => <Skeleton key={index} className="h-9" />)
        ) : error ? (
          <div className="rounded-md border p-3 text-sm">
            <p className="text-muted-foreground">Conversations could not load.</p>
            <Button className="mt-2" size="sm" variant="outline" onClick={() => void refetch()}>
              Retry
            </Button>
          </div>
        ) : filtered.length ? (
          filtered.map((conversation) => (
            <ConversationRow
              key={conversation.id}
              conversation={conversation}
              active={conversation.id === currentConversationId}
              onSelect={setCurrentConversationId}
              onRename={handleRename}
              onDelete={handleDelete}
            />
          ))
        ) : (
          <p className="px-3 py-8 text-center text-sm text-muted-foreground">
            No conversations match your search.
          </p>
        )}
      </div>
    </motion.aside>
  );
}

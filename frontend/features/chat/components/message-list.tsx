"use client";

import { memo, useEffect, useMemo, useRef } from "react";
import { motion } from "framer-motion";
import { Bot, Check, Copy, RefreshCcw, UserRound } from "lucide-react";
import ReactMarkdown, { type Components } from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight, vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Button } from "@/components/ui/button";
import type { ChatMessage } from "@/features/chat/types/chat";
import { useAppStore } from "@/store/use-app-store";
import { cn } from "@/utils/cn";

function MarkdownMessage({ content }: { content: string }) {
  const theme = useAppStore((state) => state.theme);
  const components = useMemo<Components>(
    () => ({
      ol({ children, ...props }) {
        return (
          <ol
            className="my-3 list-decimal space-y-4 pl-5 marker:font-semibold marker:text-primary"
            {...props}
          >
            {children}
          </ol>
        );
      },
      ul({ children, ...props }) {
        return (
          <ul className="my-2 list-disc space-y-1.5 pl-5 marker:text-primary" {...props}>
            {children}
          </ul>
        );
      },
      li({ children, ...props }) {
        return (
          <li className="pl-1.5 leading-6" {...props}>
            {children}
          </li>
        );
      },
      p({ children, ...props }) {
        return (
          <p className="my-2 first:mt-0 last:mb-0" {...props}>
            {children}
          </p>
        );
      },
      a({ children, href, ...props }) {
        return (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold text-primary underline decoration-primary/35 decoration-2 underline-offset-4 transition-colors hover:decoration-primary"
            {...props}
          >
            {children}
          </a>
        );
      },
      code({ className, children, ...props }) {
        const match = /language-(\w+)/.exec(className ?? "");
        const code = String(children).replace(/\n$/, "");
        if (!match)
          return (
            <code className={className} {...props}>
              {children}
            </code>
          );
        return (
          <SyntaxHighlighter
            language={match[1]}
            style={theme === "dark" ? vscDarkPlus : oneLight}
            PreTag="div"
            customStyle={{ margin: 0, borderRadius: 8, fontSize: 13 }}
          >
            {code}
          </SyntaxHighlighter>
        );
      },
    }),
    [theme],
  );

  return (
    <div className="prose-enterprise max-w-none text-sm leading-6">
      <ReactMarkdown components={components}>{content}</ReactMarkdown>
    </div>
  );
}

const MessageBubble = memo(function MessageBubble({
  message,
  onRegenerate,
  onDecision,
}: {
  message: ChatMessage;
  onRegenerate: () => void;
  onDecision: (decision: "approve" | "reject") => void;
}) {
  const copiedRef = useRef(false);
  const isAssistant = message.role === "assistant";

  async function copyMessage() {
    await navigator.clipboard.writeText(message.content);
    copiedRef.current = true;
  }

  return (
    <motion.article
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22, ease: "easeOut" }}
      className={cn(
        "group flex items-start gap-2.5 sm:gap-3",
        isAssistant ? "justify-start" : "justify-end",
      )}
    >
      {isAssistant ? (
        <div
          className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border bg-surface-raised text-primary shadow-sm ring-2 ring-background"
          aria-label="AI assistant"
        >
          <Bot className="h-4 w-4" aria-hidden />
        </div>
      ) : null}
      <div
        className={cn(
          "relative max-w-[84%] border px-4 py-2.5 text-sm leading-6 shadow-sm sm:max-w-[76%]",
          isAssistant ? "pr-20" : "pr-11",
          isAssistant
            ? "rounded-2xl rounded-tl-md bg-surface"
            : "rounded-2xl rounded-tr-md border-primary/20 bg-primary text-primary-foreground shadow-[0_8px_24px_hsl(var(--primary)/0.14)]",
          message.error && "border-destructive/40 bg-destructive/5 text-foreground",
        )}
      >
        {message.pending ? (
          <div aria-label="Assistant is responding" className="flex items-center gap-1 py-2">
            <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:120ms]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:240ms]" />
          </div>
        ) : message.error ? (
          <p className="text-sm text-destructive">{message.error}</p>
        ) : isAssistant ? (
          <>
            <MarkdownMessage content={message.content} />
            {message.streaming ? (
              <span
                className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-primary align-middle"
                aria-label="Response streaming"
              />
            ) : null}
            {message.interrupt ? (
              <div className="mt-3 rounded-md border border-amber-300/60 bg-amber-50 p-3 dark:bg-amber-400/10">
                <p className="text-xs font-semibold text-amber-900 dark:text-amber-200">
                  Approval required
                </p>
                <p className="mt-1 text-xs text-amber-800/80 dark:text-amber-200/70">
                  Review the proposed action before the assistant continues.
                </p>
                <div className="mt-2 flex gap-2">
                  <Button size="sm" onClick={() => onDecision("approve")}>
                    Approve
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => onDecision("reject")}>
                    Reject
                  </Button>
                </div>
              </div>
            ) : null}
          </>
        ) : (
          <p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p>
        )}
        {!message.pending && !message.error ? (
          <div className="absolute bottom-1 right-1 flex gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7"
              aria-label="Copy message"
              onClick={() => void copyMessage()}
            >
              {copiedRef.current ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            </Button>
            {isAssistant ? (
              <Button
                size="icon"
                variant="ghost"
                className="h-7 w-7"
                aria-label="Regenerate message"
                onClick={onRegenerate}
              >
                <RefreshCcw className="h-4 w-4" aria-hidden />
              </Button>
            ) : null}
          </div>
        ) : null}
      </div>
      {!isAssistant ? (
        <div
          className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-sm ring-2 ring-background"
          aria-label="You"
        >
          <UserRound className="h-4 w-4" aria-hidden />
        </div>
      ) : null}
    </motion.article>
  );
});

export function MessageList({
  messages,
  onRegenerate,
  onDecision = onRegenerate,
}: {
  messages: ChatMessage[];
  onRegenerate: () => void;
  onDecision?: (decision: "approve" | "reject") => void;
}) {
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (typeof scrollRef.current?.scrollIntoView === "function") {
      scrollRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [messages.length]);

  if (!messages.length) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-center">
        <div className="max-w-md">
          <h2 className="text-2xl font-semibold">Enterprise AI Document Assistant</h2>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            Create or select a conversation, upload PDFs, and ask grounded questions with markdown
            and code-aware responses.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="scrollbar-thin h-full overflow-y-auto px-3 py-6 sm:px-6 sm:py-8">
      <div className="mx-auto flex max-w-4xl flex-col gap-5">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            onRegenerate={onRegenerate}
            onDecision={onDecision}
          />
        ))}
        <div ref={scrollRef} />
      </div>
    </div>
  );
}

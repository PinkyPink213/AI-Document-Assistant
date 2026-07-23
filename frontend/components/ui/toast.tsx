"use client";

import * as ToastPrimitive from "@radix-ui/react-toast";
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { X } from "lucide-react";
import { cn } from "@/utils/cn";

export type ToastTone = "default" | "success" | "error";

interface ToastMessage {
  id: string;
  title: string;
  description?: string;
  tone: ToastTone;
}

interface ToastContextValue {
  toast: (message: Omit<ToastMessage, "id">) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<ToastMessage[]>([]);

  const toast = useCallback((message: Omit<ToastMessage, "id">) => {
    setMessages((current) => [
      ...current,
      { ...message, id: `${Date.now()}-${Math.random().toString(36).slice(2)}` },
    ]);
  }, []);

  const value = useMemo(() => ({ toast }), [toast]);

  return (
    <ToastContext.Provider value={value}>
      <ToastPrimitive.Provider swipeDirection="right">
        {children}
        {messages.map((message) => (
          <ToastPrimitive.Root
            key={message.id}
            className={cn(
              "grid w-[360px] gap-1 rounded-lg border bg-surface p-4 shadow-soft",
              message.tone === "success" && "border-pink-300 dark:border-pink-500/60",
              message.tone === "error" && "border-destructive/50",
            )}
            duration={4200}
            onOpenChange={(open) => {
              if (!open) setMessages((current) => current.filter((item) => item.id !== message.id));
            }}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <ToastPrimitive.Title className="text-sm font-semibold">
                  {message.title}
                </ToastPrimitive.Title>
                {message.description ? (
                  <ToastPrimitive.Description className="mt-1 text-sm text-muted-foreground">
                    {message.description}
                  </ToastPrimitive.Description>
                ) : null}
              </div>
              <ToastPrimitive.Close aria-label="Dismiss notification">
                <X className="h-4 w-4" aria-hidden />
              </ToastPrimitive.Close>
            </div>
          </ToastPrimitive.Root>
        ))}
        <ToastPrimitive.Viewport className="fixed bottom-4 right-4 z-50 flex max-w-[calc(100vw-2rem)] flex-col gap-2" />
      </ToastPrimitive.Provider>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  return context ?? { toast: () => undefined };
}

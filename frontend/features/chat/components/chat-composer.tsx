"use client";

import { useCallback } from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

export function ChatComposer({
  value,
  disabled,
  onChange,
  onSend,
}: {
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
  onSend: () => void;
}) {
  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        onSend();
      }
    },
    [onSend],
  );

  return (
    <div className="border-t bg-surface p-3">
      <div className="mx-auto grid max-w-4xl grid-cols-[1fr_auto] gap-2">
        <Textarea
          value={value}
          disabled={disabled}
          aria-label="Chat message"
          placeholder="Ask a question about your documents..."
          className="min-h-20"
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
        />
        <Button
          size="icon"
          className="h-20 w-12 self-stretch"
          disabled={disabled || !value.trim()}
          aria-label="Send message"
          onClick={onSend}
        >
          <Send className="h-5 w-5" aria-hidden />
        </Button>
      </div>
    </div>
  );
}

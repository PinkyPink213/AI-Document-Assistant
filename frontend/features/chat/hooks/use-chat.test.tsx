import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";
import { ToastProvider } from "@/components/ui/toast";
import { useChat } from "@/features/chat/hooks/use-chat";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>{children}</ToastProvider>
    </QueryClientProvider>
  );
}

describe("useChat", () => {
  it("loads persisted messages for the selected conversation", async () => {
    const { result } = renderHook(() => useChat(1), { wrapper: createWrapper() });

    await waitFor(() =>
      expect(
        result.current.messages.some((message) =>
          message.content.includes("steady revenue growth"),
        ),
      ).toBe(true),
    );
  });

  it("creates a pending assistant message before sending", async () => {
    const { result } = renderHook(() => useChat(1), { wrapper: createWrapper() });
    await result.current.sendMessage("Hello");
    await waitFor(() =>
      expect(
        result.current.messages.some((message) => message.content.includes("Answer for")),
      ).toBe(true),
    );
  });
});

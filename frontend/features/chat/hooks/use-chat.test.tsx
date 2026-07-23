import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";
import { ToastProvider } from "@/components/ui/toast";
import { useChat } from "@/features/chat/hooks/use-chat";
import { server } from "@/test/server";

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

  it("keeps approval visible and blocks a new message until a decision", async () => {
    let chatCalls = 0;
    server.use(
      http.post("http://127.0.0.1:8000/conversations/:id/chat", () => {
        chatCalls += 1;
        return HttpResponse.json({
          response: null,
          interrupt: {
            action_requests: [{ name: "delete_document", args: { filename: "timelen2.pdf" } }],
          },
        });
      }),
    );
    const { result } = renderHook(() => useChat(99), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isLoadingHistory).toBe(false));

    await act(async () => {
      await result.current.sendMessage("Delete timelen2.pdf");
    });

    expect(result.current.isAwaitingApproval).toBe(true);
    expect(result.current.messages.some((message) => message.interrupt)).toBe(true);

    await act(async () => {
      await result.current.sendMessage("Find external papers");
    });

    expect(chatCalls).toBe(1);
  });
});

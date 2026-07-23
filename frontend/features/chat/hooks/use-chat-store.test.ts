import { describe, expect, it } from "vitest";
import { useChatStore } from "@/features/chat/hooks/use-chat-store";

describe("useChatStore", () => {
  it("appends and updates messages", () => {
    useChatStore.getState().clearConversation(1);
    useChatStore.getState().setMessages(1, []);
    useChatStore.getState().appendMessage(1, {
      id: "m1",
      conversationId: 1,
      role: "assistant",
      content: "Thinking",
      createdAt: "2026-07-23T00:00:00Z",
      pending: true,
    });
    useChatStore.getState().updateMessage(1, "m1", { pending: false, content: "Done" });

    expect(useChatStore.getState().messagesByConversation[1][0]).toMatchObject({
      content: "Done",
      pending: false,
    });

    useChatStore.getState().clearConversation(1);
    expect(useChatStore.getState().messagesByConversation[1]).toBeUndefined();
  });

  it("handles empty conversations and leaves unrelated messages unchanged", () => {
    useChatStore.getState().clearConversation(99);
    useChatStore.getState().appendMessage(99, {
      id: "first",
      conversationId: 99,
      role: "user",
      content: "Hello",
      createdAt: "2026-07-24T00:00:00Z",
    });
    useChatStore.getState().updateMessage(99, "missing", { content: "Changed" });
    useChatStore.getState().updateMessage(100, "missing", { content: "Changed" });

    expect(useChatStore.getState().messagesByConversation[99][0].content).toBe("Hello");
    expect(useChatStore.getState().messagesByConversation[100]).toEqual([]);
  });
});

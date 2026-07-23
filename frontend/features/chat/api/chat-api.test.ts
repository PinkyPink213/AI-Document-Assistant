import { describe, expect, it } from "vitest";
import { getChatHistory, resumeChat, sendChatMessage } from "@/features/chat/api/chat-api";

describe("chat api", () => {
  it("sends a message and renders markdown-ready content", async () => {
    const response = await sendChatMessage(1, "risk summary");

    expect(response.response).toContain("risk summary");
    expect(response.response).toContain("```ts");
  });

  it("continues a response", async () => {
    await expect(resumeChat(1, "approve")).resolves.toEqual({
      response: "Continued response",
      interrupt: null,
    });
  });

  it("loads persisted conversation history", async () => {
    const history = await getChatHistory(1);

    expect(history).toHaveLength(2);
    expect(history[1]).toMatchObject({
      role: "assistant",
      content: "The filing highlights steady revenue growth.",
    });
  });
});

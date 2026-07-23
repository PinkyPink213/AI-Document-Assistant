import { describe, expect, it } from "vitest";
import {
  createConversation,
  deleteConversation,
  getConversation,
  listConversations,
  updateConversation,
} from "@/features/conversation/api/conversation-api";

describe("conversation api", () => {
  it("lists and creates conversations", async () => {
    const created = await createConversation({ title: "Board packet review" });
    const conversations = await listConversations();

    expect(created.title).toBe("Board packet review");
    expect(conversations.some((conversation) => conversation.id === created.id)).toBe(true);
    await expect(getConversation(created.id)).resolves.toMatchObject({ id: created.id });
  });

  it("updates and deletes conversations", async () => {
    const created = await createConversation({ title: "Temporary conversation" });
    const updated = await updateConversation(created.id, { title: "Renamed conversation" });

    expect(updated.title).toBe("Renamed conversation");
    await expect(deleteConversation(created.id)).resolves.toBeUndefined();
  });
});

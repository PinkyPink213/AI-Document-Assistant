import { describe, expect, it } from "vitest";
import { useAppStore } from "@/store/use-app-store";

describe("useAppStore", () => {
  it("stores ui state", () => {
    useAppStore.getState().setCurrentConversationId(42);
    useAppStore.getState().setTheme("dark");
    useAppStore.getState().setLeftSidebarOpen(false);
    useAppStore.getState().setRightSidebarOpen(false);

    expect(useAppStore.getState().currentConversationId).toBe(42);
    expect(useAppStore.getState().theme).toBe("dark");
    expect(useAppStore.getState().leftSidebarOpen).toBe(false);
    expect(useAppStore.getState().rightSidebarOpen).toBe(false);
  });
});

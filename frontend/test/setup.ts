import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll, beforeEach, vi } from "vitest";
import { useChatStore } from "@/features/chat/hooks/use-chat-store";
import { useAppStore } from "@/store/use-app-store";
import { resetTestData, server } from "@/test/server";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
beforeEach(() => {
  localStorage.clear();
  useAppStore.setState({
    currentConversationId: null,
    leftSidebarOpen: true,
    rightSidebarOpen: true,
    theme: "light",
  });
  useChatStore.setState({ messagesByConversation: {} });
});
afterEach(() => {
  cleanup();
  server.resetHandlers();
  resetTestData();
});
afterAll(() => server.close());

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

Object.defineProperty(navigator, "clipboard", {
  configurable: true,
  value: {
    writeText: vi.fn().mockResolvedValue(undefined),
  },
});

Element.prototype.scrollIntoView = vi.fn();

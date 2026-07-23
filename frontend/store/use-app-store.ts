import { create } from "zustand";
import { persist } from "zustand/middleware";

export type ThemeMode = "light" | "dark";

interface AppState {
  currentConversationId: number | null;
  leftSidebarOpen: boolean;
  rightSidebarOpen: boolean;
  theme: ThemeMode;
  setCurrentConversationId: (conversationId: number | null) => void;
  setLeftSidebarOpen: (open: boolean) => void;
  setRightSidebarOpen: (open: boolean) => void;
  setTheme: (theme: ThemeMode) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      currentConversationId: null,
      leftSidebarOpen: true,
      rightSidebarOpen: true,
      theme: "light",
      setCurrentConversationId: (conversationId) => set({ currentConversationId: conversationId }),
      setLeftSidebarOpen: (open) => set({ leftSidebarOpen: open }),
      setRightSidebarOpen: (open) => set({ rightSidebarOpen: open }),
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: "enterprise-ai-document-assistant",
      partialize: (state) => ({
        currentConversationId: state.currentConversationId,
        leftSidebarOpen: state.leftSidebarOpen,
        rightSidebarOpen: state.rightSidebarOpen,
        theme: state.theme,
      }),
    },
  ),
);

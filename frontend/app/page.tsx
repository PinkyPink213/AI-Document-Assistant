"use client";

import dynamic from "next/dynamic";
import { Menu, Moon, PanelLeftOpen, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChatPanel } from "@/features/chat/components/chat-panel";
import { ConversationSidebar } from "@/features/conversation/components/conversation-sidebar";
import { HeaderHealth } from "@/features/health/components/header-health";
import { useAppStore } from "@/store/use-app-store";
import { cn } from "@/utils/cn";

const DetailsSidebar = dynamic(
  () =>
    import("@/features/documents/components/details-sidebar").then(
      (module) => module.DetailsSidebar,
    ),
  { ssr: false },
);

export default function Home() {
  const leftSidebarOpen = useAppStore((state) => state.leftSidebarOpen);
  const rightSidebarOpen = useAppStore((state) => state.rightSidebarOpen);
  const setLeftSidebarOpen = useAppStore((state) => state.setLeftSidebarOpen);
  const theme = useAppStore((state) => state.theme);
  const setTheme = useAppStore((state) => state.setTheme);

  function toggleTheme() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.classList.toggle("dark", next === "dark");
  }

  return (
    <main className="flex h-screen min-h-[640px] flex-col overflow-hidden bg-background">
      <div className="flex h-11 items-center justify-between border-b bg-surface px-3">
        <div className="flex items-center gap-2">
          <Button
            size="icon"
            variant="ghost"
            aria-label={
              leftSidebarOpen ? "Close conversation sidebar" : "Open conversation sidebar"
            }
            onClick={() => setLeftSidebarOpen(!leftSidebarOpen)}
          >
            {leftSidebarOpen ? <Menu className="h-4 w-4" /> : <PanelLeftOpen className="h-4 w-4" />}
          </Button>
          <span className="flex items-center gap-2 text-sm font-semibold">
            <span className="h-2 w-2 rounded-full bg-primary shadow-[0_0_14px_hsl(var(--primary)/0.8)]" />
            AI PDF Document Workspace
          </span>
        </div>
        <div className="flex items-center gap-2">
          <HeaderHealth />
          <Button size="icon" variant="ghost" aria-label="Toggle dark mode" onClick={toggleTheme}>
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
        </div>
      </div>
      <div
        className={cn(
          "workspace-grid grid min-h-0 flex-1 transition-[grid-template-columns] duration-300",
          leftSidebarOpen &&
            rightSidebarOpen &&
            "workspace-grid--both grid-cols-[300px_minmax(0,1fr)_340px]",
          leftSidebarOpen &&
            !rightSidebarOpen &&
            "workspace-grid--left grid-cols-[300px_minmax(0,1fr)]",
          !leftSidebarOpen &&
            rightSidebarOpen &&
            "workspace-grid--right grid-cols-[minmax(0,1fr)_340px]",
          !leftSidebarOpen && !rightSidebarOpen && "grid-cols-1",
        )}
      >
        {leftSidebarOpen ? <ConversationSidebar /> : null}
        <ChatPanel />
        {rightSidebarOpen ? <DetailsSidebar /> : null}
      </div>
    </main>
  );
}

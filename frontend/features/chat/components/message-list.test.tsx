import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ToastProvider } from "@/components/ui/toast";
import { MessageList } from "@/features/chat/components/message-list";
import { renderWithProviders } from "@/test/render";

describe("MessageList", () => {
  it("renders empty state", () => {
    renderWithProviders(<MessageList messages={[]} onRegenerate={vi.fn()} />);

    expect(screen.getByText("Enterprise AI Document Assistant")).toBeInTheDocument();
  });

  it("renders markdown and highlighted code", () => {
    renderWithProviders(
      <ToastProvider>
        <MessageList
          onRegenerate={vi.fn()}
          messages={[
            {
              id: "a1",
              conversationId: 1,
              role: "assistant",
              content: "**Summary**\n\n```ts\nconst ready = true;\n```",
              createdAt: "2026-07-23T00:00:00Z",
            },
          ]}
        />
      </ToastProvider>,
    );

    expect(screen.getByText("Summary")).toBeInTheDocument();
    expect(screen.getByText(/ready/)).toBeInTheDocument();
    expect(screen.getByLabelText("AI assistant")).toBeInTheDocument();
  });

  it("renders human approval controls and returns the decision", async () => {
    const user = userEvent.setup();
    const onDecision = vi.fn();
    renderWithProviders(
      <MessageList
        onRegenerate={vi.fn()}
        onDecision={onDecision}
        messages={[
          {
            id: "approval-1",
            conversationId: 1,
            role: "assistant",
            content: "I am ready to update the record.",
            createdAt: "2026-07-23T00:00:00Z",
            interrupt: { action: "update_record" },
          },
        ]}
      />,
    );

    expect(screen.getByText("Approval required")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Reject" }));
    expect(onDecision).toHaveBeenCalledWith("reject");
  });
});

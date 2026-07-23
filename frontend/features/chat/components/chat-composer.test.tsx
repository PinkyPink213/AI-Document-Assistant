import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ChatComposer } from "@/features/chat/components/chat-composer";
import { renderWithProviders } from "@/test/render";

describe("ChatComposer", () => {
  it("sends with Ctrl+Enter", () => {
    const onSend = vi.fn();
    renderWithProviders(
      <ChatComposer value="hello" disabled={false} onChange={vi.fn()} onSend={onSend} />,
    );

    fireEvent.keyDown(screen.getByLabelText("Chat message"), { key: "Enter", ctrlKey: true });
    expect(onSend).toHaveBeenCalledTimes(1);
  });
});

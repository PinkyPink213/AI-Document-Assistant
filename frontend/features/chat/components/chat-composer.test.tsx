import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ChatComposer } from "@/features/chat/components/chat-composer";
import { renderWithProviders } from "@/test/render";

describe("ChatComposer", () => {
  it("sends with Enter", () => {
    const onSend = vi.fn();
    renderWithProviders(
      <ChatComposer value="hello" disabled={false} onChange={vi.fn()} onSend={onSend} />,
    );

    fireEvent.keyDown(screen.getByLabelText("Chat message"), { key: "Enter" });
    expect(onSend).toHaveBeenCalledTimes(1);
  });

  it("keeps Shift+Enter available for a new line", () => {
    const onSend = vi.fn();
    renderWithProviders(
      <ChatComposer value="hello" disabled={false} onChange={vi.fn()} onSend={onSend} />,
    );

    const event = new KeyboardEvent("keydown", {
      key: "Enter",
      shiftKey: true,
      bubbles: true,
      cancelable: true,
    });
    screen.getByLabelText("Chat message").dispatchEvent(event);

    expect(onSend).not.toHaveBeenCalled();
    expect(event.defaultPrevented).toBe(false);
  });
});

import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { ConversationSidebar } from "@/features/conversation/components/conversation-sidebar";
import { renderWithProviders } from "@/test/render";

describe("ConversationSidebar", () => {
  it("loads conversations and creates a conversation through the form", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ConversationSidebar />);

    expect(await screen.findByText("Quarterly filings")).toBeInTheDocument();
    await user.clear(screen.getByLabelText("New conversation title"));
    await user.type(screen.getByLabelText("New conversation title"), "Audit memo");
    await user.click(screen.getByRole("button", { name: /new conversation/i }));

    await waitFor(() => expect(screen.getByText("Conversation created")).toBeInTheDocument());
  });

  it("validates the create form", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ConversationSidebar />);

    await user.clear(screen.getByLabelText("New conversation title"));
    await user.type(screen.getByLabelText("New conversation title"), "AI");
    await user.click(screen.getByRole("button", { name: /new conversation/i }));

    expect(await screen.findByText("Use at least 3 characters.")).toBeInTheDocument();
  });

  it("renames and deletes a conversation", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ConversationSidebar />);

    expect(await screen.findByText("Quarterly filings")).toBeInTheDocument();
    await user.click(screen.getByLabelText("Rename conversation"));
    const title = screen.getByLabelText("Conversation title");
    await user.clear(title);
    await user.type(title, "Annual filings");
    await user.click(screen.getByLabelText("Save conversation title"));

    expect(await screen.findByText("Conversation renamed")).toBeInTheDocument();
    await user.click(screen.getByLabelText("Delete conversation"));
    expect(await screen.findByText("Conversation deleted")).toBeInTheDocument();
  });
});

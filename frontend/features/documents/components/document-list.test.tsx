import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { DocumentList } from "@/features/documents/components/document-list";
import { renderWithProviders } from "@/test/render";

describe("DocumentList", () => {
  it("renders uploaded documents", async () => {
    renderWithProviders(<DocumentList conversationId={1} />);

    expect(await screen.findByText("report.pdf")).toBeInTheDocument();
  });

  it("deletes a document and shows confirmation", async () => {
    const user = userEvent.setup();
    renderWithProviders(<DocumentList conversationId={1} />);

    await user.click(await screen.findByLabelText("Delete report.pdf"));
    expect(await screen.findByText("Document deleted")).toBeInTheDocument();
    expect(screen.queryByText("report.pdf")).not.toBeInTheDocument();
  });
});

import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DocumentUploader } from "@/features/documents/components/document-uploader";
import { renderWithProviders } from "@/test/render";

describe("DocumentUploader", () => {
  it("shows a toast for invalid files", async () => {
    renderWithProviders(<DocumentUploader conversationId={1} />);

    fireEvent.drop(screen.getByText("Drop PDF documents"), {
      dataTransfer: {
        files: [new File(["bad"], "notes.txt", { type: "text/plain" })],
        items: [
          {
            kind: "file",
            type: "text/plain",
            getAsFile: () => new File(["bad"], "notes.txt", { type: "text/plain" }),
          },
        ],
        types: ["Files"],
      },
    });

    await waitFor(() => expect(screen.getAllByText("Invalid file").length).toBeGreaterThan(0));
  });

  it("warns before uploading a duplicate filename", async () => {
    renderWithProviders(<DocumentUploader conversationId={1} />);
    expect(await screen.findByText("1 PDF already uploaded")).toBeInTheDocument();

    const duplicate = new File(["pdf"], "REPORT.PDF", { type: "application/pdf" });
    fireEvent.drop(screen.getByText("Drop PDF documents"), {
      dataTransfer: {
        files: [duplicate],
        items: [
          {
            kind: "file",
            type: "application/pdf",
            getAsFile: () => duplicate,
          },
        ],
        types: ["Files"],
      },
    });

    expect(await screen.findByText("Duplicate file")).toBeInTheDocument();
    expect(
      screen.getByText("REPORT.PDF is already uploaded in this conversation."),
    ).toBeInTheDocument();
  });
});

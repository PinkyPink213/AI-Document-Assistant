import { describe, expect, it, vi } from "vitest";
import {
  deleteDocument,
  listDocuments,
  uploadDocument,
} from "@/features/documents/api/document-api";
import { api } from "@/services/api";

describe("document api", () => {
  it("lists and deletes documents", async () => {
    const before = await listDocuments(1);

    expect(before[0]?.filename).toBe("report.pdf");
    await expect(deleteDocument(before[0].id)).resolves.toEqual({
      message: "Document deleted successfully.",
    });
  });

  it("uploads documents with multipart form data and progress", async () => {
    const post = vi.spyOn(api, "post").mockResolvedValueOnce({
      data: {
        id: 99,
        conversation_id: 1,
        filename: "brief.pdf",
        created_at: "2026-07-23T00:00:00Z",
        updated_at: "2026-07-23T00:00:00Z",
      },
    });
    const progress = vi.fn();

    const uploaded = await uploadDocument(
      1,
      new File(["pdf"], "brief.pdf", { type: "application/pdf" }),
      progress,
    );

    expect(uploaded.filename).toBe("brief.pdf");
    const config = post.mock.calls[0][2];
    config?.onUploadProgress?.({ loaded: 5, total: 10, bytes: 5, lengthComputable: true });

    expect(progress).toHaveBeenCalledWith(50);
    expect(post).toHaveBeenCalledWith(
      "/1/documents",
      expect.any(FormData),
      expect.objectContaining({
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: expect.any(Function),
      }),
    );
    post.mockRestore();
  });
});

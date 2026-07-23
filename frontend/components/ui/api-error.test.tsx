import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ApiError } from "@/components/ui/api-error";
import { renderWithProviders } from "@/test/render";

describe("ApiError", () => {
  it("renders the message and retry action", () => {
    renderWithProviders(
      <ApiError
        error={{ status: 500, message: "Backend unavailable", retryable: true }}
        onRetry={vi.fn()}
      />,
    );

    expect(screen.getByText("Request failed")).toBeInTheDocument();
    expect(screen.getByText("Backend unavailable")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });
});

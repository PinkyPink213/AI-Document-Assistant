import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import Home from "@/app/page";
import { renderWithProviders } from "@/test/render";

describe("Home page", () => {
  it("renders the workspace shell", () => {
    renderWithProviders(<Home />);

    expect(screen.getByText("AI PDF Document Workspace")).toBeInTheDocument();
    expect(screen.getByLabelText("Chat workspace")).toBeInTheDocument();
    expect(screen.getByLabelText("Conversation sidebar")).toBeInTheDocument();
  });
});

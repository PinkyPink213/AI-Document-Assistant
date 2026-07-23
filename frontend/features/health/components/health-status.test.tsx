import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { HealthStatus } from "@/features/health/components/health-status";
import { renderWithProviders } from "@/test/render";
import { server } from "@/test/server";

describe("HealthStatus", () => {
  it("renders health metrics", async () => {
    renderWithProviders(<HealthStatus />);

    expect(await screen.findByText("API")).toBeInTheDocument();
    expect(await screen.findByText("Database")).toBeInTheDocument();
  });

  it("shows an issue when the database is unavailable", async () => {
    server.use(
      http.get("http://127.0.0.1:8000/health/db", () =>
        HttpResponse.json({ status: "error", database: "disconnected" }),
      ),
    );
    renderWithProviders(<HealthStatus />);

    expect(await screen.findByText("disconnected")).toBeInTheDocument();
    expect(screen.getByText("Issue")).toBeInTheDocument();
  });
});

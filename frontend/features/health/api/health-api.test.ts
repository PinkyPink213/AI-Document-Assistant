import { describe, expect, it } from "vitest";
import { getDatabaseHealth, getHealth } from "@/features/health/api/health-api";

describe("health api", () => {
  it("loads application and database health", async () => {
    await expect(getHealth()).resolves.toMatchObject({ status: "ok" });
    await expect(getDatabaseHealth()).resolves.toMatchObject({
      status: "ok",
      database: "connected",
    });
  });
});

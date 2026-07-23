import { describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { api, toApiFailure } from "@/services/api";
import { server } from "@/test/server";

describe("api error handling", () => {
  it("normalizes unknown errors", () => {
    expect(toApiFailure(new Error("Broken"))).toEqual({
      status: 0,
      message: "Broken",
      retryable: false,
    });
  });

  it("normalizes axios response details", async () => {
    server.use(
      http.get("http://127.0.0.1:8000/bad-request", () =>
        HttpResponse.json({ detail: "Invalid request" }, { status: 400 }),
      ),
    );

    try {
      await api.get("/bad-request");
    } catch (caught) {
      expect(toApiFailure(caught)).toEqual({
        status: 400,
        message: "Invalid request",
        retryable: false,
      });
    }
  });

  it("retries retryable server failures", async () => {
    let calls = 0;
    server.use(
      http.get("http://127.0.0.1:8000/flaky", () => {
        calls += 1;
        return HttpResponse.json({ detail: [{ msg: "Still unavailable" }] }, { status: 503 });
      }),
    );

    try {
      await api.get("/flaky");
    } catch (caught) {
      expect(calls).toBe(3);
      expect(toApiFailure(caught)).toMatchObject({
        status: 503,
        message: "Still unavailable",
        retryable: true,
      });
    }
  });
});

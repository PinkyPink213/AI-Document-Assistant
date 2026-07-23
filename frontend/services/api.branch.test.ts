import { describe, expect, it } from "vitest";
import { toApiFailure } from "@/services/api";

describe("api branch handling", () => {
  it("handles axios errors without a response body", () => {
    const failure = toApiFailure({
      isAxiosError: true,
      message: "Network down",
      response: undefined,
      config: undefined,
    });

    expect(failure).toEqual({
      status: 0,
      message: "Network down",
      retryable: true,
    });
  });

  it("reads the first validation detail message from axios errors", () => {
    const failure = toApiFailure({
      isAxiosError: true,
      message: "Bad Request",
      response: {
        status: 422,
        data: {
          detail: [{ msg: "Title is required" }],
        },
      },
      config: undefined,
    });

    expect(failure).toEqual({
      status: 422,
      message: "Title is required",
      retryable: false,
    });
  });

  it("uses an API message when no detail is provided", () => {
    const failure = toApiFailure({
      isAxiosError: true,
      message: "Request failed",
      response: { status: 400, data: { message: "Invalid request" } },
      config: undefined,
    });

    expect(failure.message).toBe("Invalid request");
  });
});

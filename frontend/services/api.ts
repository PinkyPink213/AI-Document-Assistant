import axios, { AxiosError, type AxiosInstance, type AxiosRequestConfig } from "axios";
import type { ApiErrorBody, ApiFailure } from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const MAX_RETRIES = 2;

interface RetryConfig extends AxiosRequestConfig {
  retryCount?: number;
}

function extractMessage(body: ApiErrorBody | undefined, fallback: string) {
  if (!body) return fallback;
  if (typeof body.detail === "string") return body.detail;
  if (Array.isArray(body.detail) && body.detail[0]?.msg) return body.detail[0].msg;
  return body.message ?? fallback;
}

export function toApiFailure(error: unknown): ApiFailure {
  if (axios.isAxiosError<ApiErrorBody>(error)) {
    const status = error.response?.status ?? 0;
    return {
      status,
      message: extractMessage(error.response?.data, error.message || "Request failed"),
      retryable: status === 0 || status >= 500,
    };
  }

  return {
    status: 0,
    message: error instanceof Error ? error.message : "Unexpected error",
    retryable: false,
  };
}

export const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30_000,
  headers: {
    Accept: "application/json",
  },
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorBody>) => {
    const config = error.config as RetryConfig | undefined;
    const status = error.response?.status ?? 0;
    if (!config) return Promise.reject(error);

    const retryCount = config.retryCount ?? 0;
    const method = config.method?.toLowerCase();
    const shouldRetry = (status === 0 || status >= 500) && method === "get";

    if (shouldRetry && retryCount < MAX_RETRIES) {
      const nextRetryCount = retryCount + 1;
      config.retryCount = nextRetryCount;
      await new Promise((resolve) => setTimeout(resolve, 350 * nextRetryCount));
      return api(config);
    }

    return Promise.reject(error);
  },
);

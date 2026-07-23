import { api } from "@/services/api";
import type { DatabaseHealthResponse, HealthResponse } from "@/features/health/types/health";

export const healthKeys = {
  app: ["health"] as const,
  db: ["health", "db"] as const,
};

export async function getHealth() {
  const { data } = await api.get<HealthResponse>("/health");
  return data;
}

export async function getDatabaseHealth() {
  const { data } = await api.get<DatabaseHealthResponse>("/health/db");
  return data;
}

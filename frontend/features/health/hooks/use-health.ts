import { useQuery } from "@tanstack/react-query";
import { getDatabaseHealth, getHealth, healthKeys } from "@/features/health/api/health-api";

export function useHealth() {
  const app = useQuery({
    queryKey: healthKeys.app,
    queryFn: getHealth,
    refetchInterval: 30_000,
  });

  const db = useQuery({
    queryKey: healthKeys.db,
    queryFn: getDatabaseHealth,
    refetchInterval: 30_000,
  });

  return { app, db };
}

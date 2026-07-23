"use client";

import { Activity, Database } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useHealth } from "@/features/health/hooks/use-health";
import { cn } from "@/utils/cn";

function StatusPill({ ok }: { ok: boolean }) {
  return (
    <span
      className={cn(
        "rounded-full px-2 py-0.5 text-xs font-medium",
        ok
          ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-400/15 dark:text-emerald-300"
          : "bg-destructive/10 text-destructive",
      )}
    >
      {ok ? "Healthy" : "Issue"}
    </span>
  );
}

export function HealthStatus() {
  const { app, db } = useHealth();

  return (
    <div className="space-y-2">
      {[
        {
          label: "API",
          icon: Activity,
          loading: app.isLoading,
          ok: app.data?.status === "ok",
          detail: app.data?.service ?? "FastAPI service",
        },
        {
          label: "Database",
          icon: Database,
          loading: db.isLoading,
          ok: db.data?.status === "ok" && db.data.database === "connected",
          detail: db.data?.database ?? "PostgreSQL",
        },
      ].map((item) => {
        const Icon = item.icon;
        return (
          <div key={item.label} className="rounded-md border bg-surface-raised p-3">
            {item.loading ? (
              <Skeleton className="h-10" />
            ) : (
              <div className="flex items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-2">
                  <Icon className="h-4 w-4 text-muted-foreground" aria-hidden />
                  <div className="min-w-0">
                    <p className="text-sm font-medium">{item.label}</p>
                    <p className="truncate text-xs text-muted-foreground">{item.detail}</p>
                  </div>
                </div>
                <StatusPill ok={item.ok} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

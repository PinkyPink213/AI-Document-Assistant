"use client";

import { Activity, Database } from "lucide-react";
import { useHealth } from "@/features/health/hooks/use-health";
import { cn } from "@/utils/cn";

function Indicator({
  label,
  ok,
  loading,
  icon: Icon,
}: {
  label: string;
  ok: boolean;
  loading: boolean;
  icon: typeof Activity;
}) {
  return (
    <div
      className="hidden items-center gap-1.5 rounded-full border bg-surface-raised px-2.5 py-1 text-[11px] font-medium sm:flex"
      title={`${label}: ${loading ? "Checking" : ok ? "Healthy" : "Unavailable"}`}
    >
      <Icon className="h-3 w-3 text-muted-foreground" aria-hidden />
      <span>{label}</span>
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          loading ? "animate-pulse bg-amber-400" : ok ? "bg-emerald-500" : "bg-destructive",
        )}
        aria-label={`${label} ${loading ? "checking" : ok ? "healthy" : "unavailable"}`}
      />
    </div>
  );
}

export function HeaderHealth() {
  const { app, db } = useHealth();

  return (
    <div className="flex items-center gap-1.5" aria-label="System health">
      <Indicator
        label="API"
        icon={Activity}
        loading={app.isLoading}
        ok={app.data?.status === "ok"}
      />
      <Indicator
        label="Database"
        icon={Database}
        loading={db.isLoading}
        ok={db.data?.status === "ok" && db.data.database === "connected"}
      />
    </div>
  );
}

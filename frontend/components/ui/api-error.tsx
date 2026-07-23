import { RefreshCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ApiFailure } from "@/types/api";

export function ApiError({ error, onRetry }: { error: ApiFailure; onRetry?: () => void }) {
  return (
    <div role="alert" className="rounded-lg border border-destructive/30 bg-surface p-4">
      <p className="text-sm font-semibold text-destructive">Request failed</p>
      <p className="mt-1 text-sm text-muted-foreground">{error.message}</p>
      {onRetry ? (
        <Button className="mt-3" variant="outline" size="sm" onClick={onRetry}>
          <RefreshCcw className="h-4 w-4" aria-hidden />
          Retry
        </Button>
      ) : null}
    </div>
  );
}

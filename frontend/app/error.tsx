"use client";

import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ErrorPage({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-6">
      <section className="max-w-md rounded-lg border bg-surface p-6 shadow-soft">
        <AlertTriangle className="mb-4 h-8 w-8 text-destructive" aria-hidden />
        <h1 className="text-xl font-semibold">Something went wrong</h1>
        <p className="mt-2 text-sm text-muted-foreground">{error.message}</p>
        <Button className="mt-5" onClick={reset}>
          Retry
        </Button>
      </section>
    </main>
  );
}

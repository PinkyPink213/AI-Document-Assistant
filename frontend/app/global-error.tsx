"use client";

import { Button } from "@/components/ui/button";

export default function GlobalError({ reset }: { error: Error; reset: () => void }) {
  return (
    <html lang="en">
      <body>
        <main className="flex min-h-screen items-center justify-center p-6">
          <section className="max-w-md rounded-lg border bg-surface p-6">
            <h1 className="text-xl font-semibold">Application error</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              The workspace could not recover automatically.
            </p>
            <Button className="mt-5" onClick={reset}>
              Try again
            </Button>
          </section>
        </main>
      </body>
    </html>
  );
}

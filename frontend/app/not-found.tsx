import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-6">
      <section className="max-w-md rounded-lg border bg-surface p-6 shadow-soft">
        <h1 className="text-xl font-semibold">Page not found</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          The workspace route you opened does not exist.
        </p>
        <Link
          href="/"
          className="mt-5 inline-flex h-9 items-center justify-center rounded-md bg-primary px-3.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
        >
          Return to workspace
        </Link>
      </section>
    </main>
  );
}

import type { Metadata } from "next";
import { Providers } from "@/services/query-client";
import "./globals.css";

export const metadata: Metadata = {
  title: "Enterprise AI Document Assistant",
  description: "Chat with enterprise documents through a typed AI workspace.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

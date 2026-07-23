# Frontend

## Overview

This frontend provides a production-style workspace for browsing conversations, uploading PDF documents, and chatting with the backend assistant.

## Scripts

- `npm run dev` – start the Next.js development server
- `npm run test` – run Vitest tests

## Architecture

- Feature modules live under `features/` and include API, hooks, components, and types
- Shared UI primitives live under `components/ui/`
- Global app state is stored in `store/use-app-store.ts`
- Server state and caching are handled by TanStack Query via `services/query-client.tsx`

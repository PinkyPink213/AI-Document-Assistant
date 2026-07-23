import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import type { Conversation } from "@/features/conversation/types/conversation";
import type { DocumentResource } from "@/features/documents/types/document";
import type { ChatHistoryMessage } from "@/features/chat/types/chat";

const initialConversations: Conversation[] = [
  {
    id: 1,
    title: "Quarterly filings",
    created_at: "2026-07-22T12:00:00Z",
    updated_at: "2026-07-22T12:30:00Z",
  },
];

const initialDocuments: DocumentResource[] = [
  {
    id: 10,
    conversation_id: 1,
    filename: "report.pdf",
    created_at: "2026-07-22T12:00:00Z",
    updated_at: "2026-07-22T12:00:00Z",
    chunk_count: 12,
  },
];

const initialMessages: ChatHistoryMessage[] = [
  {
    id: 1,
    conversation_id: 1,
    role: "user",
    content: "Summarize the quarterly filing",
    created_at: "2026-07-22T12:35:00Z",
  },
  {
    id: 2,
    conversation_id: 1,
    role: "assistant",
    content: "The filing highlights steady revenue growth.",
    created_at: "2026-07-22T12:35:02Z",
  },
];

let conversations = structuredClone(initialConversations);
let documents = structuredClone(initialDocuments);
let messages = structuredClone(initialMessages);

export function resetTestData() {
  conversations = structuredClone(initialConversations);
  documents = structuredClone(initialDocuments);
  messages = structuredClone(initialMessages);
}

export const handlers = [
  http.get("http://127.0.0.1:8000/conversation", () => HttpResponse.json(conversations)),
  http.post("http://127.0.0.1:8000/conversation", async ({ request }) => {
    const body = (await request.json()) as { title: string };
    const conversation: Conversation = {
      id: conversations.length + 1,
      title: body.title,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    conversations = [conversation, ...conversations];
    return HttpResponse.json(conversation);
  }),
  http.get("http://127.0.0.1:8000/conversation/:id", ({ params }) => {
    const conversation = conversations.find((item) => item.id === Number(params.id));
    return conversation
      ? HttpResponse.json(conversation)
      : HttpResponse.json({ detail: "Not found" }, { status: 404 });
  }),
  http.put("http://127.0.0.1:8000/conversation/:id", async ({ params, request }) => {
    const body = (await request.json()) as { title: string };
    const id = Number(params.id);
    conversations = conversations.map((conversation) =>
      conversation.id === id ? { ...conversation, title: body.title } : conversation,
    );
    return HttpResponse.json(conversations.find((conversation) => conversation.id === id));
  }),
  http.delete("http://127.0.0.1:8000/conversation/:id", ({ params }) => {
    conversations = conversations.filter((conversation) => conversation.id !== Number(params.id));
    return new HttpResponse(null, { status: 204 });
  }),
  http.post("http://127.0.0.1:8000/conversations/:id/chat", async ({ request, params }) => {
    const body = (await request.json()) as { message: string };
    if (!body.message.trim())
      return HttpResponse.json({ detail: "Empty message" }, { status: 422 });
    const conversationId = Number(params.id);
    messages.push(
      {
        id: messages.length + 1,
        conversation_id: conversationId,
        role: "user",
        content: body.message,
        created_at: new Date().toISOString(),
      },
      {
        id: messages.length + 2,
        conversation_id: conversationId,
        role: "assistant",
        content: `Answer for **${body.message}**\n\n\`\`\`ts\nconst ok = true;\n\`\`\``,
        created_at: new Date().toISOString(),
      },
    );
    return HttpResponse.json({
      response: `Answer for **${body.message}**\n\n\`\`\`ts\nconst ok = true;\n\`\`\``,
      interrupt: null,
    });
  }),
  http.get("http://127.0.0.1:8000/conversations/:id/messages", ({ params }) =>
    HttpResponse.json(messages.filter((message) => message.conversation_id === Number(params.id))),
  ),
  http.post("http://127.0.0.1:8000/conversations/:id/chat/resume", () =>
    HttpResponse.json({ response: "Continued response", interrupt: null }),
  ),
  http.get("http://127.0.0.1:8000/:conversationId/documents", ({ params }) =>
    HttpResponse.json(
      documents.filter((document) => document.conversation_id === Number(params.conversationId)),
    ),
  ),
  http.post("http://127.0.0.1:8000/:conversationId/documents", ({ params }) => {
    const document: DocumentResource = {
      id: documents.length + 10,
      conversation_id: Number(params.conversationId),
      filename: "uploaded.pdf",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    documents = [...documents, document];
    return HttpResponse.json(document);
  }),
  http.delete("http://127.0.0.1:8000/documents/:id", ({ params }) => {
    documents = documents.filter((document) => document.id !== Number(params.id));
    return HttpResponse.json({ message: "Document deleted successfully." });
  }),
  http.all("http://127.0.0.1:8000/*", async ({ request }) => {
    const url = new URL(request.url);
    const method = request.method;
    const path = url.pathname;

    if (method === "GET" && path === "/health") {
      return HttpResponse.json({
        status: "ok",
        service: "enterprise-ai-workspace",
        timestamp: new Date().toISOString(),
      });
    }

    if (method === "GET" && path === "/health/db") {
      return HttpResponse.json({ status: "ok", database: "connected" });
    }

    if (method === "GET" && /^\/\d+\/documents$/.test(path)) {
      const conversationId = Number(path.split("/")[1]);
      return HttpResponse.json(
        documents.filter((document) => document.conversation_id === conversationId),
      );
    }

    if (method === "POST" && /^\/\d+\/documents$/.test(path)) {
      const conversationId = Number(path.split("/")[1]);
      const document: DocumentResource = {
        id: documents.length + 10,
        conversation_id: conversationId,
        filename: "uploaded.pdf",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      documents = [...documents, document];
      return HttpResponse.json(document);
    }

    if (method === "DELETE" && /^\/documents\/\d+$/.test(path)) {
      const documentId = Number(path.split("/")[2]);
      documents = documents.filter((document) => document.id !== documentId);
      return HttpResponse.json({ message: "Document deleted successfully." });
    }

    return HttpResponse.json({ detail: "Unhandled request" }, { status: 404 });
  }),
  http.get("http://127.0.0.1:8000/health", () =>
    HttpResponse.json({
      status: "ok",
      service: "enterprise-ai-workspace",
      timestamp: new Date().toISOString(),
    }),
  ),
  http.get("http://127.0.0.1:8000/health/db", () =>
    HttpResponse.json({ status: "ok", database: "connected" }),
  ),
];

export const server = setupServer(...handlers);

```
                          Browser
                              │
                              ▼
                     FastAPI (API Layer)
                              │
      ┌───────────────────────┼──────────────────────┐
      ▼                                              ▼
 Conversation API                             Document API
      │                                              │
      ▼                                              ▼
ConversationService                         DocumentService
      │                                              │
      ▼                                              ▼
ConversationRepository                     DocumentRepository
      │                                              │
      ▼                                              ▼
     SQL DB                                   SQL DB (metadata)
                                                     │
                                                     ▼
                                               IndexService
                                                     │
                                                     ▼
                                             app/ai/indexer.py
                                                     │
                     ┌───────────────────────────────┼──────────────────────────────┐
                     ▼                               ▼                              ▼
              pdf_loader.py                 text_splitter.py                 embeddings.py
                     │                               │                              │
                     └───────────────────────────────┴──────────────┐
                                                                    ▼
                                                            vectorstore.py
                                                                    │
                                                                    ▼
                                                                 Qdrant
────────────────────────────────────────────────────────────────────────────────────
                              │
                              ▼
                         POST /chat
                              │
                              ▼
                        ChatService
                              │
                              ▼
                        app/ai/rag_chain.py
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
   retriever.py          prompts.py          chat_model.py
         │                                          │
         ▼                                          ▼
      Qdrant                                   OpenAI/GPT
         │                                          │
         └────────────────────┬─────────────────────┘
                              ▼
                          Final Answer
```

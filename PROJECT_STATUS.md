# Local RAG — Project Status

Last reviewed: 30 September 2026

## Overview

Local RAG is a healthcare-focused document question-answering prototype. Users upload supported documents, the backend extracts and indexes their content, and a browser chat interface answers questions using retrieved passages. Answers include source details to help users inspect the evidence.

This is a local prototype, not a clinically validated product or a production-ready public service. .

## Technology stack

### Backend

- Python, FastAPI, and Uvicorn for the web API and static file serving.
- LangChain integrations for Ollama chat and embedding models.
- Ollama models: `qwen3:8b` is the configured chat default; `nomic-embed-text` is the embedding default. The Ollama service and required model files must be available separately.
- ChromaDB for persistent vector storage and semantic retrieval.
- `rank-bm25` for lexical keyword retrieval.
- pypdf and Python ZIP/XML/CSV handling for supported document extraction.
- Joblib for saving the BM25 index.

### Frontend

- HTML, CSS, and vanilla JavaScript.
- PDF.js for in-browser PDF viewing.

## Implemented features

- Upload PDF, DOCX, XLSX, CSV, TXT, and ZIP files containing supported documents.
- Extract document text and split it into overlapping chunks (default: 1,000 characters, 200-character overlap).
- Apply a healthcare-domain heuristic to documents and queries.
- Index chunks in Chroma for semantic retrieval and build a BM25 keyword index.
- Search in semantic, BM25/keyword, or hybrid mode. Hybrid search combines ranked results with reciprocal-rank fusion.
- Ask questions through the chat interface; return generated answers, source details, follow-up suggestions, and basic retrieval/timing metrics.
- Select a document and filter retrieval to it. Current code passes document selection through chat handling and applies document filters in semantic and keyword retrieval. The older bug report below has been removed because it no longer matches the code; multi-user behavior still needs work.
- List, view, and delete uploaded documents; navigate to cited source material.
- Export chat content as TXT, Markdown, or PDF through the frontend.
- Provide a streaming chat API endpoint (`POST /stream-chat`). The current chat UI uses `POST /chat`, so streaming is available in the backend but is not wired into the main chat flow.
- Provide a basic `GET /health` API response.

## Storage and state

- Uploaded files: `backend/uploads/`.
- Chroma database: `backend/vectorstore/`.
- BM25 index: `backend/bm25_index.pkl`.
- Active document selection and chat history are currently held in server process memory.
- Browser settings and client session identifiers use browser local storage.

## Current limitations and risks

- No Dockerfile or Docker Compose setup is currently present.
- No public deployment or public URL is configured. A shareable link requires an always-on host or hosting service, network/TLS setup, and a reachable Ollama/model service.
- The API has no visible authentication or per-user authorization. Document listing, viewing, upload, and deletion operate on shared server data.
- The active document is stored as one process-global value, so concurrent users can affect each other's selection. Chat state is also in-memory and not an authenticated user boundary.
- Do not expose the current app publicly with sensitive documents. Authentication, user/data isolation, privacy controls, and operational protections should be designed before public use.
- `GET /health` checks only whether the FastAPI route responds; it does not confirm Ollama/model or database readiness.
- Healthcare checks are heuristics. They are not clinical validation, medical advice safeguards, or a guarantee that all accepted content is relevant.
- Scanned/image-only PDFs may not provide extractable text because OCR is not implemented.
- BM25 rebuilding is synchronous and can become slow as the corpus grows.
- Retrieval confidence values are rough ranking indicators, not calibrated probabilities.
- No visible production rate limiting, audit logging, backup/restore process, or multi-instance coordination is implemented.

## Recommended next steps

### Before sharing with external users

1. Add authentication and authorization; separate documents and active-document/session state per user.
2. Define privacy and retention rules for uploaded healthcare material.
3. Add robust request/file size limits, rate limiting, error handling, logging, and backups.
4. Decide whether Ollama runs on the same host or a separate managed machine and size the host for the selected models.

### Deployment

1. Add a Dockerfile and Compose configuration for the API and Ollama (or document a remote Ollama configuration).
2. Persist uploads and vector/index data using Docker volumes.
3. Deploy to an always-on host and configure HTTPS/domain or a secure tunnel for a public URL.
4. Add readiness checks that verify dependencies, not just the API process.

### Product and quality improvements

- Verify active-document behavior with multiple sessions and make it user-scoped.
- Wire the existing streaming endpoint into the chat UI if streaming is desired.
- Add OCR if scanned PDFs are in scope.
- Evaluate retrieval relevance, answer faithfulness, citation correctness, latency, and rejection behavior on a representative question set.
- Consider background indexing and durable session storage as the corpus and user count grow.
- Reconcile this file with implementation changes during future releases.

## Demo checklist

- Confirm Ollama is running and both the configured chat and embedding models are available.
- Start the FastAPI application using the project environment and serve it locally.
- Upload a healthcare document and confirm it appears in the document list.
- Ask a question answered by the document and inspect its citations.
- Ask a question not supported by the document and explain the intended grounded-answer behavior and its limits.
- Demonstrate selecting a document and changing retrieval mode.
- Explain that the project is not yet Dockerized or safe for unauthenticated public access.

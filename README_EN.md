# LitLens: Evidence-based Literary Reading Assistant

[中文](README.md) | English

LitLens is an AI application for evidence-based literary close reading. It provides a FastAPI backend, a static reading workspace, document upload and deletion, public-domain book import, PDF/EPUB parsing, genre-aware chunking, RAG question answering, and a LangGraph-based literary agent workflow.

## Features

- FastAPI REST backend with auto-generated Swagger docs.
- Static reading workspace at `/app` for upload, import, document management, RAG Q&A, agent analysis, citations, and steps.
- OpenAI-compatible LLM and embedding APIs.
- `.env` configuration for model, proxy, database, and RAG settings.
- Upload, parse, and delete `.txt`, `.md`, `.pdf`, and `.epub` documents.
- Import public texts from Project Gutenberg / Gutendex and Wikisource.
- Genre-aware chunking for English fiction, modern Chinese prose, classical poetry, classical prose, and poetry-like texts.
- Chroma vector store with SQLite metadata and JSON fallback retrieval.
- RAG answers with citation metadata.
- LangGraph-based evidence workflow with `fast` and `deep` modes.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload
```

API docs:

```text
http://127.0.0.1:8000/docs
```

Frontend workspace:

```text
http://127.0.0.1:8000/app
```

## Configuration

Core `.env` values:

```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-api-key
LLM_MODEL_NAME=gpt-4o-mini
EMBEDDING_MODEL_NAME=text-embedding-3-small
EMBEDDING_BATCH_SIZE=16
BOOK_SOURCE_PROXY=
```

If you use a local proxy such as Clash, set:

```env
BOOK_SOURCE_PROXY=http://127.0.0.1:7897
```

If `LLM_API_KEY` is empty, the project uses local fallback responses for development.

## Common API Examples

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Search public books:

```bash
curl "http://127.0.0.1:8000/book-sources/search?source=gutenberg&q=pride%20and%20prejudice"
```

Import a Gutenberg text:

```bash
curl -X POST http://127.0.0.1:8000/book-sources/import \
  -H "Content-Type: application/json" \
  -d '{"source":"gutenberg","source_id":"1342"}'
```

Delete a document:

```bash
curl -X DELETE http://127.0.0.1:8000/documents/your-document-id
```

Ask a RAG question:

```bash
curl -X POST http://127.0.0.1:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{"document_id":"your-document-id","query":"Analyze the opening narrative tone with textual evidence."}'
```

Run the evidence-based agent workflow:

```bash
curl -X POST http://127.0.0.1:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"document_id":"your-document-id","task":"Analyze how imagery supports the central theme.","top_k":5,"mode":"deep"}'
```

`mode` options:

- `fast`: retrieve evidence and generate one concise answer.
- `deep`: run the full `plan -> retrieve -> reader -> critic -> verifier -> final` workflow.

## Architecture

```text
Upload / Import
  -> parse text / PDF / EPUB
  -> detect document type
  -> genre-aware chunking
  -> embedding
  -> Chroma + SQLite

User question
  -> retrieve citations
  -> build prompt context
  -> LLM answer
  -> return answer + citations

Agent workflow
  -> planner
  -> retriever
  -> Reader Agent
  -> Critic Agent
  -> Verifier Agent
  -> Final Writer
```

## Tests

```bash
pytest
```

The test suite covers health checks, parsing, chunking, genre detection, book-source import, RAG flow, embedding batching, frontend static serving, document deletion, and the LangGraph agent workflow.

## Roadmap

- Local library scanning and batch import for user-authorized directories.
- OCR for scanned PDFs and image-based documents.
- Claim-level evidence verification for final answers.
- Context compression and long-term reading memory for long novels.
- Character relationship graphs and event timelines.
- User accounts, bookshelves, reading progress, and note management.
- Background task queues for large parsing and embedding jobs.
- Vector database upgrades such as Milvus, Qdrant, or PostgreSQL + pgvector.
- Electron/Tauri desktop shell for richer local file access.
- Production Docker Compose, logging, monitoring, and CI/CD.

## Notes

LitLens only integrates legal public text sources. It does not connect to pirated ebook sources or DRM-bypassing services.

# LitLens: Evidence-based Literary Reading Assistant

[中文](README.md) | English

LitLens is a FastAPI-based AI backend for close reading and evidence-based literary analysis. Users can upload texts or import public-domain works, then ask questions grounded in the original text with citations.

## Features

- FastAPI REST backend with auto-generated Swagger docs.
- OpenAI-compatible LLM and embedding APIs.
- `.env` configuration for model, proxy, database, and RAG settings.
- Upload `.txt` / `.md` documents.
- Import public texts from Project Gutenberg / Gutendex and Wikisource.
- Genre-aware chunking for English fiction, modern Chinese prose, classical poetry, and classical prose.
- Chroma vector store with SQLite metadata.
- RAG answers with citation metadata.
- LangGraph-based evidence workflow: `plan -> retrieve -> reader -> critic -> verifier -> final`.

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
  -d '{"document_id":"your-document-id","task":"Analyze how imagery supports the central theme.","top_k":5}'
```

## Architecture

```text
Upload / Import
  -> parse text
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

The test suite covers health checks, chunking, genre detection, book-source import, RAG flow, embedding batching, and the LangGraph agent workflow.

## Notes

LitLens only integrates legal public text sources. It does not connect to pirated ebook sources or DRM-bypassing services.

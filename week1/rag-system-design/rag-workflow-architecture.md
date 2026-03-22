# RAG System Design — Basic Workflow Architecture

## Overview

Retrieval-Augmented Generation (RAG) is a pattern that grounds LLM responses in external knowledge by retrieving relevant documents at query time, rather than relying solely on the model's training data.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          RAG SYSTEM ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────────────┘

╔══════════════════════════════════════════╗
║           INGESTION PIPELINE             ║   (Run once / on update)
╚══════════════════════════════════════════╝

  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │  Raw Data    │────▶│  Document    │────▶│   Chunking   │
  │  Sources     │     │  Loader      │     │   Strategy   │
  │              │     │              │     │              │
  │ • PDFs       │     │ • Parse text │     │ • Fixed size │
  │ • Web pages  │     │ • Extract    │     │ • Recursive  │
  │ • Databases  │     │   metadata   │     │ • Semantic   │
  │ • APIs       │     │ • Clean text │     │ • Overlap    │
  └──────────────┘     └──────────────┘     └──────┬───────┘
                                                   │
                                                   ▼
                                        ┌──────────────────┐
                                        │ Embedding Model  │
                                        │                  │
                                        │ text → vector    │
                                        │ [0.12, -0.34 …]  │
                                        └────────┬─────────┘
                                                 │
                                                 ▼
                                        ┌──────────────────┐
                                        │  Vector Store    │
                                        │                  │
                                        │ • ChromaDB       │
                                        │ • Pinecone       │
                                        │ • pgvector       │
                                        │ • FAISS          │
                                        └──────────────────┘


╔══════════════════════════════════════════╗
║             QUERY PIPELINE               ║   (Run per user request)
╚══════════════════════════════════════════╝

  ┌──────────────┐
  │   User       │
  │   Query      │
  │              │
  │ "What is …?" │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐
  │  Query       │────▶│  Embedding   │────▶│   Vector Store       │
  │  Processing  │     │  Model       │     │   Similarity Search  │
  │              │     │              │     │                      │
  │ • Clean      │     │ Same model   │     │ • cosine similarity  │
  │ • Rewrite    │     │ as ingestion │     │ • top-k retrieval    │
  │ • Expand     │     │              │     │ • MMR / re-ranking   │
  └──────────────┘     └──────────────┘     └──────────┬───────────┘
                                                       │
                                            ┌──────────┘
                                            │  Retrieved Chunks
                                            │  (top-k documents)
                                            ▼
                               ┌────────────────────────┐
                               │    Context Assembly    │
                               │                        │
                               │  System Prompt         │
                               │  + Retrieved Chunks    │
                               │  + User Query          │
                               │  ──────────────────    │
                               │  = Final Prompt        │
                               └────────────┬───────────┘
                                            │
                                            ▼
                               ┌────────────────────────┐
                               │       LLM              │
                               │                        │
                               │ • GPT-4o               │
                               │ • Claude Sonnet        │
                               │ • Gemini Flash         │
                               │ • DeepSeek-R1 (Ollama) │
                               └────────────┬───────────┘
                                            │
                                            ▼
                               ┌────────────────────────┐
                               │   Generated Response   │
                               │                        │
                               │  Grounded answer with  │
                               │  source citations      │
                               └────────────────────────┘
```

---

## Component Breakdown

### Ingestion Pipeline

| Step | Component | Purpose |
|---|---|---|
| 1 | **Data Sources** | Raw documents — PDFs, web pages, databases, APIs |
| 2 | **Document Loader** | Parses and extracts clean text + metadata |
| 3 | **Chunking** | Splits documents into overlapping passages |
| 4 | **Embedding Model** | Converts text chunks into dense vector representations |
| 5 | **Vector Store** | Persists vectors for fast similarity search |

### Query Pipeline

| Step | Component | Purpose |
|---|---|---|
| 1 | **User Query** | Natural language question from the user |
| 2 | **Query Processing** | Optional: clean, rewrite, or expand the query |
| 3 | **Embedding Model** | Encodes the query using the same model as ingestion |
| 4 | **Similarity Search** | Retrieves top-k most relevant chunks from the vector store |
| 5 | **Context Assembly** | Builds the final prompt: system instructions + chunks + query |
| 6 | **LLM** | Generates a grounded, cited response |

---

## Key Design Decisions

### Chunking Strategy
```
Fixed-size chunking     → Simple, predictable, fast
Recursive chunking      → Respects document structure (headers, paragraphs)
Semantic chunking       → Groups by meaning, best quality, slower
Overlap                 → Prevents context loss at chunk boundaries (e.g. 20%)
```

### Retrieval Strategy
```
Dense retrieval         → Vector similarity (semantic match)
Sparse retrieval        → BM25 keyword match (exact terms)
Hybrid retrieval        → Dense + Sparse combined (best recall)
Re-ranking              → Cross-encoder reorders top-k for precision
```

### Embedding Models
```
text-embedding-3-small  → OpenAI, fast, cost-effective
text-embedding-3-large  → OpenAI, highest accuracy
nomic-embed-text        → Local via Ollama, no API cost
mxbai-embed-large       → Local, strong open-source option
```

---

## Data Flow Summary

```
Raw Docs ──▶ Loader ──▶ Chunks ──▶ Embeddings ──▶ Vector Store
                                                        │
User Query ──▶ Embed ──▶ Similarity Search ────────────┘
                                │
                         Top-k Chunks
                                │
                    System Prompt + Chunks + Query
                                │
                              LLM
                                │
                         Final Response
```

---

## Failure Points & Mitigations

| Failure | Symptom | Mitigation |
|---|---|---|
| Poor chunking | Context cut mid-sentence | Use recursive or semantic chunking with overlap |
| Embedding mismatch | Low retrieval relevance | Use same model for ingestion and query |
| Top-k too low | Missing relevant context | Increase k, add re-ranking step |
| Prompt too long | LLM truncates context | Limit chunk size, compress retrieved text |
| Stale index | Outdated answers | Trigger re-ingestion on document updates |
| Hallucination | Fabricated citations | Ground with strict system prompt, return source metadata |

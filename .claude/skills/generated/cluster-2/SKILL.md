---
name: cluster-2
description: "Skill for the Cluster_2 area of Karo. 4 symbols across 1 files."
---

# Cluster_2

4 symbols | 1 files | Cohesion: 100%

## When to Use

- Understanding how load_qmr_knowledge_documents, create_embeddings, main work
- Modifying cluster_2-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ingest.py` | _parse_chunk_fields, load_qmr_knowledge_documents, create_embeddings, main |

## Entry Points

Start here when exploring this area:

- **`load_qmr_knowledge_documents`** (Function) — `ingest.py:85`
- **`create_embeddings`** (Function) — `ingest.py:139`
- **`main`** (Function) — `ingest.py:177`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `load_qmr_knowledge_documents` | Function | `ingest.py` | 85 |
| `create_embeddings` | Function | `ingest.py` | 139 |
| `main` | Function | `ingest.py` | 177 |
| `_parse_chunk_fields` | Function | `ingest.py` | 42 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → _parse_chunk_fields` | intra_community | 3 |

## How to Explore

1. `gitnexus_context({name: "load_qmr_knowledge_documents"})` — see callers and callees
2. `gitnexus_query({query: "cluster_2"})` — find related execution flows
3. Read key files listed above for implementation details

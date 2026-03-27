---
name: backend
description: "Skill for the Backend area of Karo. 11 symbols across 3 files."
---

# Backend

11 symbols | 3 files | Cohesion: 89%

## When to Use

- Working with code in `backend/`
- Understanding how extract_response_fields, api_call_tool, run_extraction_script work
- Modifying backend-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `backend/helpers.py` | _normalize_token, _path_tokens, _matches_target, _collect_field_matches, extract_response_fields (+3) |
| `backend/agent.py` | get_agent, ask_agent |
| `backend/tools.py` | api_call_tool |

## Entry Points

Start here when exploring this area:

- **`extract_response_fields`** (Function) — `backend/helpers.py:159`
- **`api_call_tool`** (Function) — `backend/tools.py:121`
- **`run_extraction_script`** (Function) — `backend/helpers.py:48`
- **`truncate_text`** (Function) — `backend/helpers.py:92`
- **`serialize_docs`** (Function) — `backend/helpers.py:193`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `extract_response_fields` | Function | `backend/helpers.py` | 159 |
| `api_call_tool` | Function | `backend/tools.py` | 121 |
| `run_extraction_script` | Function | `backend/helpers.py` | 48 |
| `truncate_text` | Function | `backend/helpers.py` | 92 |
| `serialize_docs` | Function | `backend/helpers.py` | 193 |
| `get_agent` | Function | `backend/agent.py` | 17 |
| `ask_agent` | Function | `backend/agent.py` | 38 |
| `_normalize_token` | Function | `backend/helpers.py` | 100 |
| `_path_tokens` | Function | `backend/helpers.py` | 104 |
| `_matches_target` | Function | `backend/helpers.py` | 119 |
| `_collect_field_matches` | Function | `backend/helpers.py` | 135 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Api_call_tool → _normalize_token` | cross_community | 5 |
| `Api_call_tool → _path_tokens` | cross_community | 5 |

## How to Explore

1. `gitnexus_context({name: "extract_response_fields"})` — see callers and callees
2. `gitnexus_query({query: "backend"})` — find related execution flows
3. Read key files listed above for implementation details

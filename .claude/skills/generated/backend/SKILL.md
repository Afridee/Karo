---
name: backend
description: "Skill for the Backend area of Karo. 15 symbols across 4 files."
---

# Backend

15 symbols | 4 files | Cohesion: 97%

## When to Use

- Working with code in `backend/`
- Understanding how api_call_tool, run_extraction_script, truncate_text work
- Modifying backend-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `backend/helpers.py` | run_extraction_script, truncate_text, _normalize_token, _path_tokens, _matches_target (+3) |
| `app.py` | _find_download_url, on_chat_start, on_message, _handle_question |
| `backend/agent.py` | get_agent, ask_agent |
| `backend/tools.py` | api_call_tool |

## Entry Points

Start here when exploring this area:

- **`api_call_tool`** (Function) — `backend/tools.py:121`
- **`run_extraction_script`** (Function) — `backend/helpers.py:48`
- **`truncate_text`** (Function) — `backend/helpers.py:92`
- **`extract_response_fields`** (Function) — `backend/helpers.py:159`
- **`on_chat_start`** (Function) — `app.py:76`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `api_call_tool` | Function | `backend/tools.py` | 121 |
| `run_extraction_script` | Function | `backend/helpers.py` | 48 |
| `truncate_text` | Function | `backend/helpers.py` | 92 |
| `extract_response_fields` | Function | `backend/helpers.py` | 159 |
| `on_chat_start` | Function | `app.py` | 76 |
| `on_message` | Function | `app.py` | 291 |
| `serialize_docs` | Function | `backend/helpers.py` | 193 |
| `get_agent` | Function | `backend/agent.py` | 17 |
| `ask_agent` | Function | `backend/agent.py` | 38 |
| `_normalize_token` | Function | `backend/helpers.py` | 100 |
| `_path_tokens` | Function | `backend/helpers.py` | 104 |
| `_matches_target` | Function | `backend/helpers.py` | 119 |
| `_collect_field_matches` | Function | `backend/helpers.py` | 135 |
| `_find_download_url` | Function | `app.py` | 53 |
| `_handle_question` | Function | `app.py` | 298 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Api_call_tool → _normalize_token` | intra_community | 5 |
| `Api_call_tool → _path_tokens` | intra_community | 5 |
| `On_audio_chunk → Get_agent` | cross_community | 4 |
| `On_audio_chunk → _find_download_url` | cross_community | 4 |
| `On_audio_chunk → Serialize_docs` | cross_community | 4 |
| `On_audio_end → Get_agent` | cross_community | 4 |
| `On_audio_end → _find_download_url` | cross_community | 4 |
| `On_audio_end → Serialize_docs` | cross_community | 4 |
| `On_message → Get_agent` | intra_community | 3 |
| `On_message → _find_download_url` | intra_community | 3 |

## How to Explore

1. `gitnexus_context({name: "api_call_tool"})` — see callers and callees
2. `gitnexus_query({query: "backend"})` — find related execution flows
3. Read key files listed above for implementation details

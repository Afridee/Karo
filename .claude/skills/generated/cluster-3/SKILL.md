---
name: cluster-3
description: "Skill for the Cluster_3 area of Karo. 6 symbols across 1 files."
---

# Cluster_3

6 symbols | 1 files | Cohesion: 92%

## When to Use

- Understanding how on_audio_chunk, on_audio_end work
- Modifying cluster_3-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `app.py` | _pcm_to_wav, _rms_int16, _audio_sample_rate, _transcribe_and_respond, on_audio_chunk (+1) |

## Entry Points

Start here when exploring this area:

- **`on_audio_chunk`** (Function) — `app.py:222`
- **`on_audio_end`** (Function) — `app.py:274`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `on_audio_chunk` | Function | `app.py` | 222 |
| `on_audio_end` | Function | `app.py` | 274 |
| `_pcm_to_wav` | Function | `app.py` | 119 |
| `_rms_int16` | Function | `app.py` | 130 |
| `_audio_sample_rate` | Function | `app.py` | 136 |
| `_transcribe_and_respond` | Function | `app.py` | 153 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `On_audio_chunk → Get_agent` | cross_community | 4 |
| `On_audio_chunk → _find_download_url` | cross_community | 4 |
| `On_audio_chunk → Serialize_docs` | cross_community | 4 |
| `On_audio_end → Get_agent` | cross_community | 4 |
| `On_audio_end → _find_download_url` | cross_community | 4 |
| `On_audio_end → Serialize_docs` | cross_community | 4 |
| `On_audio_chunk → _audio_sample_rate` | intra_community | 3 |
| `On_audio_chunk → _pcm_to_wav` | intra_community | 3 |
| `On_audio_end → _audio_sample_rate` | intra_community | 3 |
| `On_audio_end → _pcm_to_wav` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Backend | 1 calls |

## How to Explore

1. `gitnexus_context({name: "on_audio_chunk"})` — see callers and callees
2. `gitnexus_query({query: "cluster_3"})` — find related execution flows
3. Read key files listed above for implementation details

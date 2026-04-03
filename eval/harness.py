"""
Load eval cases and validate retrieval docs / agent responses.

Used by eval/run_eval.py and tests/test_agent_eval.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml
from langchain_core.documents import Document


def cases_path() -> Path:
    return Path(__file__).resolve().parent / "cases.yaml"


def load_cases() -> Dict[str, Any]:
    raw = cases_path().read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError("cases.yaml must parse to a mapping")
    return data


def check_retrieval_docs(
    docs: List[Document], expect: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []
    min_docs = int(expect.get("min_docs", 1))
    if len(docs) < min_docs:
        errors.append(f"expected at least {min_docs} docs, got {len(docs)}")

    if not docs:
        return errors

    for sub in expect.get("any_doc_contains", []) or []:
        if not any(sub in (d.page_content or "") for d in docs):
            errors.append(f"no retrieved doc contained substring: {sub!r}")

    return errors


def check_agent_result(
    result: Dict[str, Any], expect: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []
    artifacts = result.get("artifacts") or {}
    sem = artifacts.get("semantic_search_docs") or []

    min_sem = int(expect.get("min_semantic_docs", 0))
    if len(sem) < min_sem:
        errors.append(f"expected min_semantic_docs={min_sem}, got {len(sem)}")

    combined_sem = "\n".join(
        f"{d.get('title') or ''}\n{d.get('preview') or ''}" for d in sem
    )
    for sub in expect.get("semantic_preview_or_title_contains", []) or []:
        if sub not in combined_sem:
            errors.append(
                f"semantic docs missing substring in title/preview: {sub!r}"
            )

    answer = str(result.get("answer") or "")
    for sub in expect.get("answer_contains", []) or []:
        if sub not in answer:
            errors.append(f"answer missing substring: {sub!r}")

    apis = artifacts.get("api_responses") or []
    min_api = int(expect.get("min_api_responses", 0))
    if len(apis) < min_api:
        errors.append(f"expected min_api_responses={min_api}, got {len(apis)}")

    return errors


def summarize_case(case_id: str, errors: List[str]) -> Tuple[bool, str]:
    if not errors:
        return True, f"PASS  {case_id}"
    return False, f"FAIL  {case_id}\n  " + "\n  ".join(errors)

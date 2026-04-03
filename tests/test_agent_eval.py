"""Eval harness tests — same cases as eval/cases.yaml."""

from __future__ import annotations

import os

import pytest

from eval.harness import (
    check_agent_result,
    check_retrieval_docs,
    load_cases,
)


@pytest.mark.parametrize(
    "case",
    load_cases().get("retrieval_cases") or [],
    ids=lambda c: c["id"],
)
def test_retrieval_case(case):
    from backend.tools import vectorstore

    docs = vectorstore.similarity_search(case["query"], k=5)
    errors = check_retrieval_docs(docs, case.get("expect") or {})
    assert not errors, "\n".join(errors)


@pytest.mark.agent
@pytest.mark.parametrize(
    "case",
    load_cases().get("agent_cases") or [],
    ids=lambda c: c["id"],
)
@pytest.mark.asyncio
async def test_agent_case(case):
    from backend.agent import ask_agent

    tid = case.get("thread_id") or f"eval-{case['id']}"
    result = await ask_agent(case["question"], thread_id=tid)
    errors = check_agent_result(result, case.get("expect") or {})
    assert not errors, "\n".join(errors)


_integration = os.getenv("KARO_EVAL_API") == "1" and bool(os.getenv("API_TOKEN"))


@pytest.mark.integration
@pytest.mark.skipif(not _integration, reason="Set KARO_EVAL_API=1 and API_TOKEN to run")
@pytest.mark.parametrize(
    "case",
    load_cases().get("integration_cases") or [],
    ids=lambda c: c["id"],
)
@pytest.mark.asyncio
async def test_integration_case(case):
    from backend.agent import ask_agent

    tid = case.get("thread_id") or f"eval-{case['id']}"
    result = await ask_agent(case["question"], thread_id=tid)
    errors = check_agent_result(result, case.get("expect") or {})
    assert not errors, "\n".join(errors)

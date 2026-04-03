#!/usr/bin/env python3
"""
Run Karo eval cases from the command line (no pytest required).

Usage (from repo root):
  uv sync --group dev
  uv run python eval/run_eval.py
  uv run python eval/run_eval.py --retrieval-only

Requires the same .env as the app (DATABASE_URL, OPENAI_API_KEY, BASE_URL, etc.).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
load_dotenv(_ROOT / ".env")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run Karo eval cases")
    p.add_argument(
        "--retrieval-only",
        action="store_true",
        help="Skip agent and integration cases",
    )
    p.add_argument(
        "--integration",
        action="store_true",
        help="Run integration cases (needs API_TOKEN and KARO_EVAL_API=1)",
    )
    return p.parse_args()


async def _main_async(args: argparse.Namespace) -> int:
    from backend.agent import ask_agent
    from backend.tools import vectorstore

    from eval.harness import (
        check_agent_result,
        check_retrieval_docs,
        load_cases,
        summarize_case,
    )

    data = load_cases()
    failed = 0

    for case in data.get("retrieval_cases") or []:
        cid = case["id"]
        query = case["query"]
        expect = case.get("expect") or {}
        docs = vectorstore.similarity_search(query, k=5)
        errs = check_retrieval_docs(docs, expect)
        ok, msg = summarize_case(cid, errs)
        print(msg)
        if not ok:
            failed += 1

    if args.retrieval_only:
        return 1 if failed else 0

    for case in data.get("agent_cases") or []:
        cid = case["id"]
        q = case["question"]
        tid = case.get("thread_id") or f"eval-{cid}"
        expect = case.get("expect") or {}
        result = await ask_agent(q, thread_id=tid)
        errs = check_agent_result(result, expect)
        ok, msg = summarize_case(cid, errs)
        print(msg)
        if not ok:
            failed += 1

    if args.integration and os.getenv("KARO_EVAL_API") == "1" and os.getenv(
        "API_TOKEN"
    ):
        for case in data.get("integration_cases") or []:
            cid = case["id"]
            q = case["question"]
            tid = case.get("thread_id") or f"eval-{cid}"
            expect = case.get("expect") or {}
            result = await ask_agent(q, thread_id=tid)
            errs = check_agent_result(result, expect)
            ok, msg = summarize_case(cid, errs)
            print(msg)
            if not ok:
                failed += 1
    elif args.integration:
        print(
            "SKIP  integration (set KARO_EVAL_API=1 and API_TOKEN to run)",
        )

    return 1 if failed else 0


def main() -> None:
    args = _parse_args()
    try:
        code = asyncio.run(_main_async(args))
    except Exception as exc:  # noqa: BLE001
        print(f"eval/run_eval.py aborted: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    raise SystemExit(code)


if __name__ == "__main__":
    main()

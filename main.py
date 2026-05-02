"""CLI entry point for the Pydantic AI Deep Research Agent."""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from agent import AgentDeps, build_deep_research_agent, run_deep_research
from tools import KnowledgeBase


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pydantic AI Deep Research Agent")
    parser.add_argument("query", nargs="*", help="Research question")
    parser.add_argument("--docs-path", default=os.getenv("DOCS_PATH", "docs.md"))
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "openai:gpt-4.1-mini"))
    parser.add_argument("--max-context-chars", type=int, default=int(os.getenv("MAX_CONTEXT_CHARS", "9000")))
    return parser.parse_args()


async def _run() -> None:
    load_dotenv(override=True)
    args = _parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required in environment or .env file.")

    query = " ".join(args.query).strip()
    if not query:
        query = input("Enter research query: ").strip()
    if not query:
        raise ValueError("A non-empty research query is required.")

    kb = KnowledgeBase(Path(args.docs_path))
    deps = AgentDeps(kb=kb, max_context_chars=args.max_context_chars)
    agent = build_deep_research_agent(model=args.model)

    result = await run_deep_research(agent=agent, deps=deps, query=query)
    print(result)


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()

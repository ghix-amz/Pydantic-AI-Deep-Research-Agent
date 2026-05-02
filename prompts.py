"""Prompt templates for the deep research agent."""

from __future__ import annotations

import json
from typing import Any


DEEP_RESEARCH_SYSTEM_PROMPT = """
You are a Deep Research Agent.

Your job is to produce a structured, detailed report grounded in provided search evidence.
Rules:
1) Be explicit about uncertainty and conflicting claims.
2) Prefer primary sources for financial claims (earnings release, SEC filings, investor relations).
3) For each major claim, provide an evidence bullet with citation in this format:
   [URL | Source Title]
4) Do not invent citations. If evidence is weak, say so.
5) Keep sections clear and non-overlapping.
"""


def build_research_prompt(
    *,
    user_query: str,
    intent: str,
    ticker: str | None,
    ticker_context: str,
    docs_context: str,
    initial_discovery: list[dict[str, Any]],
    angle_payload: list[dict[str, Any]],
) -> str:
    """Compose user prompt with all gathered research artifacts."""
    return f"""
Input query:
{user_query}

Detected intent: {intent}
Detected ticker: {ticker or "N/A"}
Resolved ticker context:
{ticker_context or "N/A"}

Relevant local docs context:
{docs_context or "N/A"}

Initial DuckDuckGo discovery results:
{json.dumps(initial_discovery, indent=2, ensure_ascii=True)}

Parallel deep-dive results by angle:
{json.dumps(angle_payload, indent=2, ensure_ascii=True)}

Write a detailed report with these sections and order:
1. Executive Summary
2. Angle-by-Angle Findings
   - For each angle: key findings and evidence bullets with citations [URL | Source Title]
3. Risks, Uncertainties, and Conflicting Information
4. What to Watch Next (5-8 bullets)

Style constraints:
- Be specific and cite concrete numbers where available.
- Separate fact from interpretation.
- If a source appears low quality or secondary, flag it.
- Keep output in plain markdown.
"""

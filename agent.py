from dataclasses import dataclass
from pydantic_ai import Agent, RunContext

from prompts import DEEP_RESEARCH_SYSTEM_PROMPT
from tools import KnowledgeBase, format_context


@dataclass
class AgentDeps:
    kb: KnowledgeBase
    max_context_chars: int = 9000


def build_deep_research_agent(model: str) -> Agent:
    agent = Agent(
        model=model,
        system_prompt=DEEP_RESEARCH_SYSTEM_PROMPT,
    )

    @agent.tool
    def retrieve_context(ctx: RunContext[AgentDeps], query: str) -> str:
        chunks = ctx.deps.kb.search(query=query)
        if not chunks:
            return "No relevant context found."
        return format_context(
            chunks, max_chars=ctx.deps.max_context_chars
        )

    return agent


async def run_deep_research(agent: Agent, deps: AgentDeps, query: str) -> str:
    try:
        chunks = deps.kb.search(query=query)
        context = format_context(
            chunks, max_chars=deps.max_context_chars
        )

        prompt = f"""
You are a deep research AI.

User Query:
{query}

Context:
{context if context else "No local context available."}

Provide a structured research report with:
- Executive Summary
- Key Findings
- Risks / Limitations
- Conclusion
"""

        result = await agent.run(prompt, deps=deps)
        return result.output or "No response generated."

    except Exception as e:
        return f"Agent error: {str(e)}"
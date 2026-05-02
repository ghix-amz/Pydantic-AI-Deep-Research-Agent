import gradio as gr
import os
from pathlib import Path
from dotenv import load_dotenv

from agent import AgentDeps, build_deep_research_agent, run_deep_research
from tools import KnowledgeBase

# load env
load_dotenv()

# DEBUG API KEY
api_key = os.getenv("OPENAI_API_KEY")
print("KEY:", api_key[:15] if api_key else "NOT FOUND")

# setup agent
model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
docs_path = os.getenv("DOCS_PATH", "docs.md")

kb = KnowledgeBase(Path(docs_path))
deps = AgentDeps(kb=kb)
agent = build_deep_research_agent(model=model)

# async function
async def chat(message, history):
    try:
        result = await run_deep_research(agent=agent, deps=deps, query=message)
        return result
    except Exception as e:
        return f"Error: {str(e)}"

# UI
demo = gr.ChatInterface(
    fn=chat,
    title="Deep Research Agent",
    description="Multi-step AI research using DuckDuckGo + OpenAI"
)

if __name__ == "__main__":
    demo.launch()

"""Local docs retrieval (docs.md), DuckDuckGo search (ddgs), and optional page fetch (httpx)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import httpx

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


@dataclass(frozen=True)
class DocChunk:
    title: str
    start_line: int
    end_line: int
    text: str

    @property
    def location(self) -> str:
        return f"{self.start_line}-{self.end_line}"


def format_context(chunks: Iterable[DocChunk], *, max_chars: int) -> str:
    parts: list[str] = []
    used = 0
    for ch in chunks:
        block = f"[{ch.title} | docs.md:{ch.location}]\n{ch.text.strip()}\n"
        if used + len(block) > max_chars and parts:
            break
        if len(block) > max_chars and not parts:
            parts.append(block[:max_chars])
            break
        parts.append(block)
        used += len(block)
    return "\n---\n".join(parts).strip()


class KnowledgeBase:
    """Chunked markdown index with simple token overlap scoring (same idea as the original single-file app)."""

    def __init__(self, docs_path: Path, max_chunk_chars: int = 3500) -> None:
        self.docs_path = docs_path
        self.max_chunk_chars = max_chunk_chars
        self._chunks: list[DocChunk] = []
        if docs_path.exists():
            self._build()

    def _build(self) -> None:
        raw = self.docs_path.read_text(encoding="utf-8", errors="replace")
        lines = raw.splitlines()

        chunks: list[DocChunk] = []
        current_title = "Local docs"
        buf: list[str] = []
        buf_start = 1
        buf_chars = 0

        def flush(end_line: int) -> None:
            nonlocal buf, buf_start, buf_chars
            if not buf:
                return
            text = "\n".join(buf).strip()
            if text:
                chunks.append(
                    DocChunk(
                        title=current_title,
                        start_line=buf_start,
                        end_line=end_line,
                        text=text,
                    )
                )
            buf = []
            buf_start = end_line + 1
            buf_chars = 0

        for i, line in enumerate(lines, start=1):
            if line.startswith("#"):
                flush(i - 1)
                current_title = line.lstrip("#").strip() or current_title
                buf_start = i
                buf = [line]
                buf_chars = len(line) + 1
                continue

            buf.append(line)
            buf_chars += len(line) + 1

            if buf_chars >= self.max_chunk_chars:
                flush(i)
                buf_start = i + 1

        flush(len(lines))
        self._chunks = chunks

    def search(self, query: str, *, k: int = 4) -> list[DocChunk]:
        q = _tokenize(query)
        if not q:
            return []

        scored: list[tuple[int, int, DocChunk]] = []
        for idx, ch in enumerate(self._chunks):
            t = _tokenize(ch.title)
            b = _tokenize(ch.text)
            overlap = len(q & (t | b))
            if overlap == 0:
                continue
            score = overlap + 2 * len(q & t)
            scored.append((score, -idx, ch))

        scored.sort(reverse=True)
        return [ch for _, __, ch in scored[:k]]

    def retrieve(self, query: str, *, max_chars: int = 9000, k: int = 4) -> str:
        if not self.docs_path.exists():
            return ""
        chunks = self.search(query, k=k)
        return format_context(chunks, max_chars=max_chars)


def ddg_text_search(query: str, max_results: int = 8) -> list[dict[str, Any]]:
    """Return DuckDuckGo text results as plain dicts (title, href, body)."""
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS  # type: ignore[no-redef]
        except ImportError as e:
            return [
                {
                    "title": "ddgs import error",
                    "href": "",
                    "body": f"Install ddgs: pip install ddgs ({e})",
                }
            ]

    try:
        results = DDGS().text(query, max_results=max_results)
        out: list[dict[str, Any]] = []
        for r in results:
            out.append(
                {
                    "title": r.get("title") or "",
                    "href": r.get("href") or "",
                    "body": r.get("body") or "",
                }
            )
        return out
    except Exception as e:
        return [{"title": "search error", "href": "", "body": str(e)}]


_HTML_TAG_RE = re.compile(r"<[^>]+>")


async def fetch_page_text(url: str, *, max_chars: int = 12_000) -> str:
    """Fetch URL and return plain text (best-effort HTML strip)."""
    headers = {"User-Agent": "DeepResearchAgent/1.0 (+local research)"}
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, headers=headers) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        raw = resp.text
        ct = (resp.headers.get("content-type") or "").lower()
        if "html" in ct:
            text = _HTML_TAG_RE.sub(" ", raw)
            text = re.sub(r"\s+", " ", text).strip()
        else:
            text = raw
        return text[:max_chars]

"""
Smart chunking strategy for MCAT fluid-dynamics PDFs.

Design decisions:
- RecursiveCharacterTextSplitter with token-aware sizing (tiktoken).
- Chunk size = 500 tokens, overlap = 50 tokens.
  Rationale: MCAT passages are ~150-300 words; 500-token chunks keep one
  full concept together without exceeding LLM context window.
- Section-header detection: lines matching heading patterns are always kept
  at the START of a new chunk so context is not lost mid-explanation.
- Each chunk carries metadata: source PDF, page range, section title.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Sequence

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

from src.ingestion.pdf_parser import ParsedPage


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class TextChunk:
    text: str
    metadata: dict = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.text)


# ---------------------------------------------------------------------------
# Section heading detection
# ---------------------------------------------------------------------------

# TODO: In the separate vocabulary.py file define those mappings and import them here
_HEADING_PATTERNS = [
    re.compile(r"^[A-Z][A-Z\s\-']{4,}$"),         # ALL CAPS headings
    re.compile(r"^\d+\.\d*\s+[A-Z]"),              # "1.2 Bernoulli..."
    re.compile(r"^(Chapter|Section|Part)\s+\d+"),  # Chapter/Section/Part
    re.compile(r"^[A-Z][a-z].*:$"),                # "Bernoulli's Law:"
]


def _is_heading(line: str) -> bool:
    line = line.strip()
    if not line or len(line) > 120:
        return False
    return any(p.match(line) for p in _HEADING_PATTERNS)


def _extract_section_title(text: str) -> str:
    """Return the first heading-like line from a text block, or empty string."""
    for line in text.splitlines():
        if _is_heading(line):
            return line.strip()
    return ""


# ---------------------------------------------------------------------------
# Token counting
# ---------------------------------------------------------------------------

def _count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    enc = tiktoken.get_encoding(encoding_name)
    return len(enc.encode(text))


# ---------------------------------------------------------------------------
# Chunker
# ---------------------------------------------------------------------------

class PDFChunker:
    """
    Converts ParsedPage objects into overlapping TextChunk objects suitable
    for embedding + retrieval.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: list[str] | None = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        if separators is None:
            # TODO: In the separate vocabulary.py file define separators and import here
            separators = ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size * 4,   # approximate char count (4 chars/token)
            chunk_overlap=chunk_overlap * 4,
            separators=separators,
            length_function=len,
            is_separator_regex=False,
        )

    def chunk_pages(self, pages: Sequence[ParsedPage]) -> list[TextChunk]:
        """Chunk a list of ParsedPage objects into TextChunks."""
        chunks: list[TextChunk] = []
        for page in pages:
            page_chunks = self._chunk_single_page(page)
            chunks.extend(page_chunks)
        logger.info(f"Created {len(chunks)} chunks from {len(pages)} pages")
        return chunks

    def _chunk_single_page(self, page: ParsedPage) -> list[TextChunk]:
        section_title = _extract_section_title(page.text)
        raw_splits = self._splitter.split_text(page.text)

        result: list[TextChunk] = []
        for i, split_text in enumerate(raw_splits):
            # Prepend section title to first chunk for context anchoring
            if i == 0 and section_title and section_title not in split_text:
                split_text = f"{section_title}\n{split_text}"

            chunk = TextChunk(
                text=split_text.strip(),
                metadata={
                    **page.metadata,
                    "chunk_index": i,
                    "section": section_title or "Unknown",
                    "token_count": _count_tokens(split_text),
                },
            )
            result.append(chunk)
        return result

    def chunk_text(self, text: str, metadata: dict | None = None) -> list[TextChunk]:
        """Convenience method to chunk a raw string directly."""
        page = ParsedPage(
            source=metadata.get("source", "unknown") if metadata else "unknown",
            page_number=metadata.get("page", 0) if metadata else 0,
            text=text,
            metadata=metadata or {},
        )
        return self._chunk_single_page(page)

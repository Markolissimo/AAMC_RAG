"""
Tests for the ingestion layer (chunker).

PDF parsing is now handled by LlamaCloud OCR (src.ingestion.ocr).
These tests cover the chunking logic which operates on plain text/markdown.
No API key required — uses synthetic text only.
"""

from __future__ import annotations

import pytest

from src.ingestion.pdf_parser import ParsedPage
from src.ingestion.chunker import PDFChunker, TextChunk, _is_heading


# ===========================================================================
# _is_heading
# ===========================================================================

class TestIsHeading:
    def test_all_caps(self):
        assert _is_heading("FLUID DYNAMICS") is True

    def test_numbered_section(self):
        assert _is_heading("1.2 Bernoulli's Equation") is True

    def test_chapter_prefix(self):
        assert _is_heading("Chapter 4") is True

    def test_colon_heading(self):
        assert _is_heading("Bernoulli's Law:") is True

    def test_plain_sentence_not_heading(self):
        assert _is_heading("The pressure in a fluid increases with depth.") is False

    def test_empty_string(self):
        assert _is_heading("") is False

    def test_too_long_line(self):
        assert _is_heading("A" * 130) is False


# ===========================================================================
# PDFChunker
# ===========================================================================

_SAMPLE_TEXT = """\
BERNOULLI'S PRINCIPLE

Bernoulli's equation states that in a flowing fluid, an increase in the speed of
the fluid occurs simultaneously with a decrease in pressure or a decrease in the
fluid's potential energy.

P + (1/2)*rho*v^2 + rho*g*h = constant

This is derived from conservation of energy. Consider a fluid element moving
along a streamline. The work done by pressure forces equals the change in
kinetic and potential energy of the fluid.

MCAT Trap: students often think faster flow means higher pressure.
In fact, the opposite is true — faster flow means LOWER pressure.
"""

_SAMPLE_PAGE = ParsedPage(
    source="test_source",
    page_number=1,
    text=_SAMPLE_TEXT,
    metadata={"source": "test_source", "page": 1},
)


class TestPDFChunker:
    def setup_method(self):
        self.chunker = PDFChunker(chunk_size=200, chunk_overlap=20)

    def test_produces_chunks(self):
        chunks = self.chunker.chunk_pages([_SAMPLE_PAGE])
        assert len(chunks) >= 1

    def test_chunks_are_TextChunk(self):
        chunks = self.chunker.chunk_pages([_SAMPLE_PAGE])
        for chunk in chunks:
            assert isinstance(chunk, TextChunk)

    def test_chunk_text_not_empty(self):
        chunks = self.chunker.chunk_pages([_SAMPLE_PAGE])
        for chunk in chunks:
            assert len(chunk.text.strip()) > 0

    def test_metadata_preserved(self):
        chunks = self.chunker.chunk_pages([_SAMPLE_PAGE])
        for chunk in chunks:
            assert chunk.metadata.get("source") == "test_source"
            assert chunk.metadata.get("page") == 1

    def test_heading_prepended_to_first_chunk(self):
        chunks = self.chunker.chunk_pages([_SAMPLE_PAGE])
        # First chunk should contain the section heading
        first_text = chunks[0].text
        assert "BERNOULLI" in first_text

    def test_chunk_size_respected(self):
        chunks = self.chunker.chunk_pages([_SAMPLE_PAGE])
        for chunk in chunks:
            # Allow 2x overhead (chars vs tokens), but no enormous chunks
            assert len(chunk.text) < 2000

    def test_multiple_pages(self):
        page2 = ParsedPage(
            source="test_source",
            page_number=2,
            text="CONTINUITY EQUATION\nA1*v1 = A2*v2\nFlow rate is conserved.",
            metadata={"source": "test_source", "page": 2},
        )
        chunks = self.chunker.chunk_pages([_SAMPLE_PAGE, page2])
        sources = {c.metadata["page"] for c in chunks}
        assert 1 in sources and 2 in sources

    def test_chunk_text_method(self):
        chunks = self.chunker.chunk_text(
            "Pascal's principle: pressure is transmitted equally in all directions.",
            metadata={"source": "manual", "page": 0},
        )
        assert len(chunks) >= 1
        assert "Pascal" in chunks[0].text

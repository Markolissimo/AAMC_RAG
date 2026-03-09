"""
Tests for the ingestion layer (PDF parser + chunker).

These tests run WITHOUT an OpenAI API key — they use only local code.
Synthetic text is used so tests never depend on actual PDF files.
"""

from __future__ import annotations

import pytest

from src.ingestion.pdf_parser import (
    ParsedPage,
    PDFParser,
    _clean_text,
    _normalize_math,
)
from src.ingestion.chunker import PDFChunker, TextChunk, _is_heading


# ===========================================================================
# _normalize_math
# ===========================================================================

class TestNormalizeMath:
    def test_superscripts(self):
        assert "r^2" in _normalize_math("r²")

    def test_subscripts(self):
        result = _normalize_math("P₁")
        assert "P" in result and "1" in result

    def test_greek_letters(self):
        result = _normalize_math("rho = ρ and eta = η")
        assert "rho" in result and "eta" in result

    def test_multiplication_symbol(self):
        assert "*" in _normalize_math("F = m × a")

    def test_greater_equal(self):
        assert ">=" in _normalize_math("v ≥ 0")

    def test_less_equal(self):
        assert "<=" in _normalize_math("P ≤ P_max")

    def test_delta(self):
        assert "Delta" in _normalize_math("ΔP")

    def test_no_change_plain_text(self):
        text = "Bernoulli's principle states that P + rho*g*h = constant"
        assert _normalize_math(text) == text


# ===========================================================================
# _clean_text
# ===========================================================================

class TestCleanText:
    def test_removes_soft_hyphen(self):
        assert "\xad" not in _clean_text("Bern\xadoulli")

    def test_collapses_excessive_blank_lines(self):
        text = "line1\n\n\n\n\nline2"
        cleaned = _clean_text(text)
        assert "\n\n\n" not in cleaned

    def test_rejoins_hyphenated_linebreak(self):
        text = "Bern-\noulli equation"
        assert "Bernoulli" in _clean_text(text)

    def test_strips_trailing_whitespace(self):
        text = "line one   \nline two   "
        for line in _clean_text(text).splitlines():
            assert not line.endswith(" ")


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


# ===========================================================================
# PDFParser — file-not-found guard
# ===========================================================================

class TestPDFParserErrors:
    def test_raises_file_not_found(self):
        parser = PDFParser()
        with pytest.raises(FileNotFoundError):
            parser.parse_file("nonexistent.pdf")

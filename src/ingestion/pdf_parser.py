"""
PDF parser with math/equation preservation.

Uses PyMuPDF (fitz) for robust text extraction. Key challenge: equations in
PDFs come out as fragmented characters. Strategy:
  1. Extract blocks with bbox metadata to detect inline vs display math.
  2. Normalize common math notations to plain-text LaTeX-safe strings.
  3. Tag each extracted page with source + page number for citation.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import fitz  # PyMuPDF
from loguru import logger

# Set Tesseract data path for OCR if not already set
# DELETE THIS! IT IS NOT A GOOD PRACTICE
if "TESSDATA_PREFIX" not in os.environ:
    tesseract_path = Path(r"C:\Users\Mark\AppData\Local\Programs\Tesseract-OCR\tessdata")
    if tesseract_path.exists():
        os.environ["TESSDATA_PREFIX"] = str(tesseract_path)


@dataclass
class ParsedPage:
    source: str          # filename stem
    page_number: int     # 1-indexed
    text: str            # cleaned text content
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Math normalization helpers
# ---------------------------------------------------------------------------

# Superscript / subscript unicode -> ASCII
_SUPERSCRIPTS = str.maketrans({
    "⁰": "^0", "¹": "^1", "²": "^2", "³": "^3", "⁴": "^4",
    "⁵": "^5", "⁶": "^6", "⁷": "^7", "⁸": "^8", "⁹": "^9",
    "⁺": "^+", "⁻": "^-", "⁼": "^=", "⁽": "^(", "⁾": "^)",
    "ⁿ": "^n",
})
_SUBSCRIPTS   = str.maketrans({
    "₀": "_0", "₁": "_1", "₂": "_2", "₃": "_3", "₄": "_4",
    "₅": "_5", "₆": "_6", "₇": "_7", "₈": "_8", "₉": "_9",
    "₊": "_+", "₋": "_-", "₌": "_=", "₍": "_(", "₎": "_)",
})

_GREEK = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta",
    "ε": "epsilon", "η": "eta", "θ": "theta", "λ": "lambda",
    "μ": "mu", "ν": "nu", "π": "pi", "ρ": "rho",
    "σ": "sigma", "τ": "tau", "φ": "phi", "ω": "omega",
    "Δ": "Delta", "Σ": "Sigma", "Ω": "Omega", "∞": "infinity",
}

_MATH_SYMBOLS = {
    "≈": "≈", "≤": "<=", "≥": ">=", "≠": "!=",
    "×": "*", "÷": "/", "√": "sqrt(", "∫": "integral",
    "∑": "sum", "∂": "partial", "∇": "nabla",
}


def _normalize_math(text: str) -> str:
    """Convert unicode math characters to ASCII-safe equivalents."""
    text = text.translate(_SUPERSCRIPTS)
    text = text.translate(_SUBSCRIPTS)
    for unicode_char, ascii_rep in _GREEK.items():
        text = text.replace(unicode_char, ascii_rep)
    for symbol, rep in _MATH_SYMBOLS.items():
        text = text.replace(symbol, rep)
    return text


def _clean_text(text: str) -> str:
    """Remove PDF extraction artefacts while preserving equation structure."""
    # Remove soft hyphens & zero-width spaces
    text = text.replace("\xad", "").replace("\u200b", "")
    # Collapse multiple blank lines to two
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Rejoin hyphenated line-breaks (e.g. "Bern-\noulli" → "Bernoulli")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # Keep intentional newlines but strip trailing whitespace per line
    lines = [line.rstrip() for line in text.splitlines()]
    text = "\n".join(lines)
    return text.strip()


# ---------------------------------------------------------------------------
# Core parser
# ---------------------------------------------------------------------------

class PDFParser:
    """Extract text from a PDF, page by page, with math normalization."""

    def __init__(self, normalize_math: bool = True):
        self.normalize_math = normalize_math

    def _extract_page_text(self, page: fitz.Page) -> str:
        raw_text = page.get_text("text")
        if raw_text.strip():
            return raw_text

        if page.get_images(full=True):
            try:
                text_page = page.get_textpage_ocr(language="eng")
                raw_text = page.get_text("text", textpage=text_page)
            except Exception as exc:
                raise RuntimeError(
                    "This PDF appears to be image-based/scanned and requires OCR. "
                    "Install Tesseract OCR and ensure it is available on PATH, then retry ingestion."
                ) from exc

        return raw_text

    def parse_file(self, pdf_path: str | Path) -> list[ParsedPage]:
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        logger.info(f"Parsing PDF: {pdf_path.name}")
        pages: list[ParsedPage] = []

        with fitz.open(str(pdf_path)) as doc:
            source = pdf_path.stem
            for page_idx in range(len(doc)):
                page = doc[page_idx]
                raw_text = self._extract_page_text(page)

                if self.normalize_math:
                    raw_text = _normalize_math(raw_text)

                cleaned = _clean_text(raw_text)

                if not cleaned:
                    continue

                pages.append(ParsedPage(
                    source=source,
                    page_number=page_idx + 1,
                    text=cleaned,
                    metadata={
                        "source": source,
                        "page": page_idx + 1,
                        "pdf_path": str(pdf_path),
                    },
                ))

        logger.info(f"Extracted {len(pages)} pages from {pdf_path.name}")
        return pages

    def parse_directory(self, directory: str | Path) -> list[ParsedPage]:
        """Parse all PDFs in a directory."""
        directory = Path(directory)
        all_pages: list[ParsedPage] = []
        for pdf_file in sorted(directory.glob("*.pdf")):
            all_pages.extend(self.parse_file(pdf_file))
        return all_pages

    def iter_pages(self, pdf_path: str | Path) -> Iterator[ParsedPage]:
        """Lazy generator for memory-efficient processing."""
        yield from self.parse_file(pdf_path)

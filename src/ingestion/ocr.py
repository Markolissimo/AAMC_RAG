"""
LlamaCloud OCR module.

Replaces PyMuPDF-based PDF parsing with LlamaCloud agentic-tier OCR.
Produces per-page markdown content and saves a full-document markdown file.

Usage:
    result = parse_pdf("./my_doc.pdf", save_to="./docs/")
    for page in result.pages:
        print(page.page_id, page.page_number, page.text[:200])
"""

from __future__ import annotations

import asyncio
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class OCRPage:
    page_number: int            # 1-indexed
    text: str                   # markdown text for this page
    page_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class OCRResult:
    doc_id: str
    filename: str
    full_markdown: str
    pages: list[OCRPage]
    md_path: Path | None = None


# ---------------------------------------------------------------------------
# Async core
# ---------------------------------------------------------------------------

async def _parse_pdf_async(pdf_path: Path, api_key: str) -> OCRResult:
    from llama_cloud import AsyncLlamaCloud  # type: ignore

    doc_id = str(uuid.uuid4())
    client = AsyncLlamaCloud(api_key=api_key)

    logger.info(f"Uploading '{pdf_path.name}' to LlamaCloud…")
    file_obj = await client.files.create(
        file=str(pdf_path),
        purpose="parse",
    )

    logger.info(f"Parsing '{pdf_path.name}' with agentic-tier OCR (this may take a minute)…")
    result = await client.parsing.parse(
        file_id=file_obj.id,
        tier="agentic",
        version="latest",
        expand=["markdown_full", "markdown"],
    )

    full_markdown: str = getattr(result, "markdown_full", "") or ""

    # --- Extract per-page markdown -------------------------------------------
    pages: list[OCRPage] = []

    raw_pages = getattr(result, "pages", None) or getattr(result, "items", None)
    if raw_pages:
        for i, pg in enumerate(raw_pages, 1):
            text = (
                getattr(pg, "markdown", "")
                or getattr(pg, "text", "")
                or ""
            )
            pages.append(OCRPage(page_number=i, text=text))
    elif full_markdown:
        # Fallback: no per-page split available — treat whole doc as page 1
        logger.warning("LlamaCloud returned no per-page content; treating full doc as single page.")
        pages.append(OCRPage(page_number=1, text=full_markdown))

    logger.info(f"OCR complete: {len(pages)} page(s) for '{pdf_path.name}'.")
    return OCRResult(
        doc_id=doc_id,
        filename=pdf_path.name,
        full_markdown=full_markdown,
        pages=pages,
    )


# ---------------------------------------------------------------------------
# Public sync API
# ---------------------------------------------------------------------------

def parse_pdf(
    pdf_path: str | Path,
    api_key: str | None = None,
    save_to: str | Path | None = None,
) -> OCRResult:
    """
    Parse a PDF via LlamaCloud OCR (agentic tier) and optionally save markdown.

    Args:
        pdf_path:  Path to the source PDF.
        api_key:   LlamaCloud API key (falls back to LLAMA_CLOUD_API_KEY env var).
        save_to:   Directory in which to save the full-doc markdown file.
                   File name: <pdf_stem>.md

    Returns:
        OCRResult with doc_id, per-page OCRPage list, and full_markdown.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    api_key = api_key or os.environ.get("LLAMA_CLOUD_API_KEY", "")
    if not api_key:
        raise ValueError("LLAMA_CLOUD_API_KEY is not set.")

    result = asyncio.run(_parse_pdf_async(pdf_path, api_key))

    if save_to:
        save_dir = Path(save_to)
        save_dir.mkdir(parents=True, exist_ok=True)
        md_path = save_dir / f"{pdf_path.stem}.md"
        md_path.write_text(result.full_markdown, encoding="utf-8")
        result.md_path = md_path
        logger.info(f"Markdown saved → {md_path}")

    return result

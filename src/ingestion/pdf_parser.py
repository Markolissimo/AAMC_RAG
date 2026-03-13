"""
ParsedPage dataclass — retained for backward compatibility with chunker.

PDF parsing is now handled by LlamaCloud OCR: see src/ingestion/ocr.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ParsedPage:
    source: str          # filename stem or doc_id
    page_number: int     # 1-indexed
    text: str            # markdown text content (from LlamaCloud OCR)
    metadata: dict = field(default_factory=dict)

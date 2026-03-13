"""
Document registry — lightweight JSON-backed two-table store.

Table 1: documents  {doc_id, filename, created_at, md_path, page_count}
Table 2: pages      {page_id, doc_id, page_number, text_preview}

Stored as:
    data/documents.json
    data/pages.json
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

from src.ingestion.ocr import OCRResult

_DATA_DIR = Path(__file__).parent.parent.parent / "data"
_DOCS_FILE  = _DATA_DIR / "documents.json"
_PAGES_FILE = _DATA_DIR / "pages.json"

_PREVIEW_LEN = 200   # chars stored as text_preview per page


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load(path: Path) -> list[dict]:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save(path: Path, data: list[dict]) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def register_document(result: OCRResult) -> dict:
    """
    Add a document entry to documents.json.
    Returns the new document record.
    """
    docs = _load(_DOCS_FILE)

    record = {
        "doc_id":     result.doc_id,
        "filename":   result.filename,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "md_path":    str(result.md_path) if result.md_path else None,
        "page_count": len(result.pages),
    }
    docs.append(record)
    _save(_DOCS_FILE, docs)
    logger.info(f"Registered document: {result.filename} (doc_id={result.doc_id})")
    return record


def register_pages(result: OCRResult) -> list[dict]:
    """
    Add per-page entries to pages.json.
    Returns the list of new page records.
    """
    pages_table = _load(_PAGES_FILE)

    new_records: list[dict] = []
    for page in result.pages:
        record = {
            "page_id":      page.page_id,
            "doc_id":       result.doc_id,
            "page_number":  page.page_number,
            "text_preview": page.text[:_PREVIEW_LEN],
        }
        pages_table.append(record)
        new_records.append(record)

    _save(_PAGES_FILE, pages_table)
    logger.info(f"Registered {len(new_records)} page(s) for doc_id={result.doc_id}")
    return new_records


def register(result: OCRResult) -> tuple[dict, list[dict]]:
    """Register both document and pages in one call."""
    doc_record  = register_document(result)
    page_records = register_pages(result)
    return doc_record, page_records


def list_documents() -> list[dict]:
    """Return all document records."""
    return _load(_DOCS_FILE)


def get_pages(doc_id: str) -> list[dict]:
    """Return all page records for a given doc_id."""
    return [p for p in _load(_PAGES_FILE) if p["doc_id"] == doc_id]


def document_exists(filename: str) -> bool:
    """Return True if a document with this filename is already registered."""
    return any(d["filename"] == filename for d in _load(_DOCS_FILE))


def remove_document(doc_id: str) -> bool:
    """
    Remove a document and all its pages from the registry.
    Returns True if the document was found and removed, False otherwise.
    """
    # Remove from documents.json
    docs = _load(_DOCS_FILE)
    original_count = len(docs)
    docs = [d for d in docs if d["doc_id"] != doc_id]
    
    if len(docs) == original_count:
        logger.warning(f"Document not found: doc_id={doc_id}")
        return False
    
    _save(_DOCS_FILE, docs)
    
    # Remove all pages for this doc_id from pages.json
    pages = _load(_PAGES_FILE)
    pages_before = len(pages)
    pages = [p for p in pages if p["doc_id"] != doc_id]
    pages_removed = pages_before - len(pages)
    _save(_PAGES_FILE, pages)
    
    logger.info(f"Removed document doc_id={doc_id} and {pages_removed} page(s)")
    return True

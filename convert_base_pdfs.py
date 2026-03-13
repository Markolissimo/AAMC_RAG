"""
One-time script to convert base PDFs to markdown using LlamaCloud OCR.
Run this locally before deploying to Render.

Usage:
    python scripts/convert_base_pdfs.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from src.ingestion.ocr import parse_pdf

DOCS_DIR = Path(__file__).parent / "docs"
BASE_PDFS = [
    "Source-EK Fluid Dynamics.pdf",
    "Source-Princeton Fluid Dynamics.pdf",
]

def main():
    llama_key = os.getenv("LLAMA_CLOUD_API_KEY")
    if not llama_key:
        print("❌ LLAMA_CLOUD_API_KEY not found in .env")
        return
    
    for pdf_name in BASE_PDFS:
        pdf_path = DOCS_DIR / pdf_name
        if not pdf_path.exists():
            print(f"⚠️  {pdf_name} not found, skipping...")
            continue
        
        md_name = pdf_path.stem + ".md"
        md_path = DOCS_DIR / md_name
        
        if md_path.exists():
            print(f"✅ {md_name} already exists, skipping...")
            continue
        
        print(f"🔄 Converting {pdf_name}...")
        try:
            result = parse_pdf(pdf_path, api_key=llama_key, save_to=DOCS_DIR)
            print(f"✅ Created {md_name}")
        except Exception as e:
            print(f"❌ Failed to convert {pdf_name}: {e}")
    
    print("\n✅ Done! Base markdown files are ready for deployment.")

if __name__ == "__main__":
    main()

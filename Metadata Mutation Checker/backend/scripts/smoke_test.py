"""Smoke test: generate synthetic PDFs and run them through the analyzer.

Run from the project root:

    source .venv/bin/activate
    python backend/scripts/smoke_test.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pypdf import PdfWriter  # noqa: E402

from app.analyzer import analyze_document  # noqa: E402


def make_pdf(metadata: dict[str, str]) -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    if metadata:
        writer.add_metadata(metadata)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def main() -> None:
    cases = [
        (
            "clean_word_export.pdf",
            {
                "/Title": "Quarterly Report",
                "/Author": "Jane Doe",
                "/Subject": "Q3 Results",
                "/Creator": "Microsoft® Word for Microsoft 365",
                "/Producer": "Microsoft® Word for Microsoft 365",
                "/CreationDate": "D:20240115093000-05'00'",
                "/ModDate": "D:20240115093000-05'00'",
            },
        ),
        (
            "edited_in_acrobat.pdf",
            {
                "/Title": "Contract",
                "/Author": "Jane Doe",
                "/Creator": "Microsoft® Word for Microsoft 365",
                "/Producer": "Adobe Acrobat Pro 24.1",
                "/CreationDate": "D:20240115093000-05'00'",
                "/ModDate": "D:20250203120500-05'00'",
            },
        ),
        (
            "modified_before_created.pdf",
            {
                "/Title": "Anomaly",
                "/Creator": "Adobe Photoshop 2024",
                "/Producer": "Canva",
                "/CreationDate": "D:20240301000000Z",
                "/ModDate": "D:20231101000000Z",
            },
        ),
        ("stripped_metadata.pdf", {}),
    ]

    for name, meta in cases:
        raw = make_pdf(meta)
        report = analyze_document(raw, name, "application/pdf")
        print("=" * 72)
        print(name)
        print("-" * 72)
        d = report.model_dump()
        d.pop("extracted_metadata", None)
        print(json.dumps(d, indent=2, default=str))


if __name__ == "__main__":
    main()

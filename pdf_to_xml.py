#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

try:
    from PyPDF2 import PdfReader
except ImportError as exc:
    raise SystemExit("Missing dependency: PyPDF2. Install with: pip install pypdf2") from exc


try:
    import pytesseract  # type: ignore
    from PIL import Image  # type: ignore
    from pdf2image import convert_from_path  # type: ignore
except Exception:
    pytesseract = None
    Image = None
    convert_from_path = None


def build_xml(pages: list[dict]) -> ET.Element:
    root = ET.Element("document")
    for page in pages:
        page_el = ET.SubElement(root, "page")
        ET.SubElement(page_el, "number").text = str(page["number"])
        text_el = ET.SubElement(page_el, "text")
        for para in [p.strip() for p in page["text"].split("\n\n") if p.strip()]:
            ET.SubElement(text_el, "p").text = para
    return root


def write_xml(root: ET.Element, output_path: Path) -> None:
    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract text from PDF and write to XML. Optional OCR for image-only pages."
    )
    parser.add_argument("pdf", help="Input PDF file")
    parser.add_argument(
        "-o",
        "--output",
        default="pdf.xml",
        help="Output XML file (default: pdf.xml)",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Start page (1-based). If omitted, start from first page.",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=0,
        help="End page (1-based, inclusive). If omitted, go to last page.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Read all pages (overrides --start/--end)",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Use OCR for pages with no extractable text (requires pdf2image+pytesseract)",
    )
    parser.add_argument(
        "--lang",
        default="fas",
        help="Tesseract language code (default: fas for Persian)",
    )
    parser.add_argument(
        "--tesseract-cmd",
        default="",
        help="Full path to tesseract executable (optional)",
    )
    parser.add_argument(
        "--tessdata-dir",
        default="",
        help="Path to tessdata directory (optional)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="DPI for OCR image rendering (default: 300)",
    )
    return parser.parse_args(argv)


def _ensure_ocr_ready(args: argparse.Namespace) -> None:
    if pytesseract is None or convert_from_path is None:
        raise SystemExit(
            "OCR dependencies missing. Install with: pip install pytesseract pillow pdf2image"
        )
    if args.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = args.tesseract_cmd
    if args.tessdata_dir:
        os.environ["TESSDATA_PREFIX"] = args.tessdata_dir


def ocr_page(pdf_path: Path, page_number: int, dpi: int, lang: str) -> str:
    # pdf2image expects 1-based page numbers
    images = convert_from_path(
        str(pdf_path),
        dpi=dpi,
        first_page=page_number,
        last_page=page_number,
    )
    if not images:
        return ""
    return pytesseract.image_to_string(images[0], lang=lang)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    pdf_path = Path(args.pdf)
    if not pdf_path.is_file():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 2

    reader = PdfReader(str(pdf_path))
    total_pages = len(reader.pages)

    if args.all or (args.start == 0 and args.end == 0):
        start = 1
        end = total_pages
    else:
        start = max(1, args.start)
        end = args.end if args.end > 0 else total_pages
        if end < start:
            print("End page must be >= start page", file=sys.stderr)
            return 2

    if args.ocr:
        _ensure_ocr_ready(args)

    pages: list[dict] = []
    for i in range(start, end + 1):
        page = reader.pages[i - 1]
        text = page.extract_text() or ""
        if args.ocr and not text.strip():
            text = ocr_page(pdf_path, i, args.dpi, args.lang)
        pages.append({"number": i, "text": text})

    root = build_xml(pages)
    write_xml(root, Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

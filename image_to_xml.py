#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

try:
    from PIL import Image
except ImportError as exc:
    raise SystemExit("Missing dependency: pillow. Install with: pip install pillow") from exc

try:
    import pytesseract
except ImportError as exc:
    raise SystemExit("Missing dependency: pytesseract. Install with: pip install pytesseract") from exc


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


def iter_images(folder: Path) -> list[Path]:
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    files.sort()
    return files


def ocr_image(path: Path, lang: str) -> str:
    with Image.open(path) as img:
        return pytesseract.image_to_string(img, lang=lang)


def build_xml(items: list[dict]) -> ET.Element:
    root = ET.Element("document")
    for item in items:
        page_el = ET.SubElement(root, "page")
        ET.SubElement(page_el, "image").text = item["image"]
        text_el = ET.SubElement(page_el, "text")
        for para in [p.strip() for p in item["text"].split("\n\n") if p.strip()]:
            ET.SubElement(text_el, "p").text = para
    return root


def write_xml(root: ET.Element, output_path: Path) -> None:
    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OCR all images in a folder and write the extracted text to XML."
    )
    parser.add_argument("folder", help="Folder containing images")
    parser.add_argument(
        "-o",
        "--output",
        default="ocr.xml",
        help="Output XML file (default: ocr.xml)",
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
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"Folder not found: {folder}", file=sys.stderr)
        return 2
    if args.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = args.tesseract_cmd
    if args.tessdata_dir:
        os.environ["TESSDATA_PREFIX"] = args.tessdata_dir

    images = iter_images(folder)
    if not images:
        print("No images found.", file=sys.stderr)
        return 2

    items = []
    for path in images:
        text = ocr_image(path, args.lang)
        items.append({"image": str(path), "text": text})

    root = build_xml(items)
    write_xml(root, Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

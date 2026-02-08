#!/usr/bin/env python3
from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from typing import Dict


def build_default_map() -> Dict[str, str]:
    mapping = {
        # Extended Latin
        "ā": "ا",
        "ī": "ي",
        "ū": "و",
        "ō": "و",
        "ē": "ي",
        "š": "ش",
        "č": "چ",
        "ž": "ژ",
        "ǰ": "ج",
        "ġ": "غ",
        "ḥ": "ح",
        "ṣ": "ص",
        "ḍ": "ض",
        "ṭ": "ط",
        "ẓ": "ظ",
        "ʿ": "ع",
        "ʾ": "ء",
        # Basic Latin to Arabic/Persian letters (approximate)
        "a": "ا",
        "b": "ب",
        "c": "ک",
        "d": "د",
        "e": "e",
        "f": "ف",
        "g": "گ",
        "h": "ه",
        "i": "ي",
        "j": "ج",
        "k": "ک",
        "l": "ل",
        "m": "م",
        "n": "ن",
        "o": "و",
        "p": "پ",
        "q": "ق",
        "r": "ر",
        "s": "س",
        "t": "ت",
        "u": "و",
        "v": "و",
        "w": "و",
        "x": "خ",
        "y": "ي",
        "z": "ز",
    }

    # Add uppercase variants
    for k, v in list(mapping.items()):
        if k.isalpha():
            mapping[k.upper()] = v

    return mapping


def transform_text(text: str, mapping: Dict[str, str]) -> str:
    if not text:
        return text
    out = []
    for ch in text:
        out.append(mapping.get(ch, ch))
    return "".join(out)


def convert_xml(input_path: str, output_path: str) -> None:
    mapping = build_default_map()
    tree = ET.parse(input_path)
    root = tree.getroot()

    for elem in root.iter():
        if elem.text:
            elem.text = transform_text(elem.text, mapping)
        if elem.tail:
            elem.tail = transform_text(elem.tail, mapping)

    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert XML text nodes to Arabic using a default character map."
    )
    parser.add_argument("input", help="Input XML file")
    parser.add_argument(
        "-o",
        "--output",
        default="arabic.xml",
        help="Output XML file (default: arabic.xml)",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    convert_xml(args.input, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))

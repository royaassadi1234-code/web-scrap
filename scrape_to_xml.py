#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
import time
from html.parser import HTMLParser
from typing import List, Optional
from urllib.parse import urlparse, urlunparse, urljoin
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


BLOCK_TAGS = {
    "p",
    "div",
    "br",
    "li",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "tr",
    "td",
    "th",
    "section",
    "article",
    "header",
    "footer",
    "main",
    "aside",
    "nav",
    "blockquote",
    "pre",
}

SKIP_TAGS = {"script", "style", "noscript", "svg", "canvas", "iframe", "head"}


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._chunks: List[str] = []
        self._title: Optional[str] = None
        self._in_title = False

    @property
    def title(self) -> str:
        return self._title or ""

    def get_text(self) -> str:
        text = "".join(self._chunks)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS:
            self._skip_depth += 1
            return
        if tag == "title":
            self._in_title = True
        if tag == "br":
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
            return
        if tag == "title":
            self._in_title = False
        if tag in BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        if self._in_title:
            title = data.strip()
            if title:
                self._title = title
            return
        text = data.strip()
        if text:
            self._chunks.append(text + " ")


def fetch_html(url: str, timeout_s: float, max_bytes: int) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; SimpleScraper/1.0)",
            "Accept-Language": "fa,en;q=0.8",
        },
    )
    with urlopen(req, timeout=timeout_s) as resp:
        raw = resp.read(max_bytes)
        charset = resp.headers.get_content_charset() or "utf-8"
    try:
        return raw.decode(charset, errors="strict")
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="replace")


def split_paragraphs(text: str) -> List[str]:
    parts = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    return parts


def build_xml(url: str, title: str, text: str) -> ET.Element:
    root = ET.Element("document")
    ET.SubElement(root, "url").text = url
    ET.SubElement(root, "title").text = title
    text_el = ET.SubElement(root, "text")
    for para in split_paragraphs(text):
        ET.SubElement(text_el, "p").text = para
    return root


def build_xml_pages(pages: List[dict]) -> ET.Element:
    root = ET.Element("document")
    for page in pages:
        page_el = ET.SubElement(root, "page")
        ET.SubElement(page_el, "url").text = page["url"]
        ET.SubElement(page_el, "title").text = page["title"]
        text_el = ET.SubElement(page_el, "text")
        for para in split_paragraphs(page["text"]):
            ET.SubElement(text_el, "p").text = para
    return root


def write_xml(root: ET.Element, output_path: str) -> None:
    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme:
        parsed = parsed._replace(scheme="https")
    return urlunparse(parsed)


def cache_key(url: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", url)


def read_cache(cache_dir: str, url: str) -> Optional[str]:
    path = f"{cache_dir}/{cache_key(url)}.html"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def write_cache(cache_dir: str, url: str, html: str) -> None:
    import os

    os.makedirs(cache_dir, exist_ok=True)
    path = f"{cache_dir}/{cache_key(url)}.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch a URL and extract readable text into XML."
    )
    parser.add_argument("url", help="Page URL to scrape")
    parser.add_argument(
        "-o",
        "--output",
        default="output.xml",
        help="Output XML file path (default: output.xml)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Seconds to wait before fetching (default: 0)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Network timeout in seconds (default: 20)",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=2_000_000,
        help="Max bytes to read from the response (default: 2000000)",
    )
    parser.add_argument(
        "--cache-dir",
        default=".cache",
        help="Directory to store cached responses (default: .cache)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable cache and always fetch",
    )
    parser.add_argument(
        "--follow-next",
        action="store_true",
        help="Follow a 'next' link and append pages to the XML",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=25,
        help="Max pages to follow when using --follow-next (default: 25)",
    )
    return parser.parse_args(argv)


class NextLinkFinder(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_anchor = False
        self._current_href: Optional[str] = None
        self.next_href: Optional[str] = None

    def handle_starttag(self, tag: str, attrs) -> None:
        if self.next_href is not None:
            return
        tag = tag.lower()
        attrs_dict = {k.lower(): v for k, v in attrs if k}
        if tag == "a":
            self._in_anchor = True
            self._current_href = attrs_dict.get("href")
            if attrs_dict.get("rel") == "next" and self._current_href:
                self.next_href = self._current_href
        elif tag == "img" and self._in_anchor and self._current_href:
            alt = (attrs_dict.get("alt") or "").strip().lower()
            if alt in {"next", "next part", "next page"}:
                self.next_href = self._current_href

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a":
            self._in_anchor = False
            self._current_href = None


def find_next_url(html: str, base_url: str) -> Optional[str]:
    finder = NextLinkFinder()
    finder.feed(html)
    if not finder.next_href:
        return None
    return urljoin(base_url, finder.next_href)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    url = normalize_url(args.url)
    pages: List[dict] = []
    seen_urls = set()
    for _ in range(max(1, args.max_pages)):
        if url in seen_urls:
            break
        seen_urls.add(url)
        html = None
        if not args.no_cache:
            html = read_cache(args.cache_dir, url)
        if html is None:
            if args.delay > 0:
                time.sleep(args.delay)
            html = fetch_html(url, args.timeout, args.max_bytes)
            if not args.no_cache:
                write_cache(args.cache_dir, url, html)
        extractor = TextExtractor()
        extractor.feed(html)
        pages.append({"url": url, "title": extractor.title, "text": extractor.get_text()})
        if not args.follow_next:
            break
        next_url = find_next_url(html, url)
        if not next_url:
            break
        url = normalize_url(next_url)
    root = build_xml_pages(pages) if args.follow_next else build_xml(pages[0]["url"], pages[0]["title"], pages[0]["text"])
    write_xml(root, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

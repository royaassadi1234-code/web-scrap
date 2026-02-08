# Web Scraper to XML

Simple CLI scraper that fetches a page, extracts readable text (including Persian), and writes an XML file.

## Usage

```bash
python3 scrape_to_xml.py "https://realpython.com/python-web-scraping-practical-introduction/#build-your-first-web-scraper" -o realpython.xml
```

### Follow next pages

```bash
python3 scrape_to_xml.py "https://example.com/page1.html" --follow-next --max-pages 50 -o output.xml
```

## Image OCR to XML

### Install dependencies

Tesseract (binary) must be installed, plus Python packages.

macOS (Homebrew):

```bash
brew install tesseract tesseract-lang
```

Windows:

1. Install Tesseract from the official installer (UB Mannheim build is common).
2. During install, add Tesseract to PATH.
3. Install language data for Persian (`fas`) if not included.

Python packages:

```bash
pip install pytesseract pillow
```

### Run image to xml

```bash
python3 image_to_xml.py C:\Users\royassadi\Documents\Roya_Drive_C\Iranistik\Benedikt\Druz\main_sources\DD2\DD2-20260204T182020Z-3-001\DD2  -o ocr.xml --lang fas  --tesseract-cmd "C:\Program Files\Tesseract-OCR\tesseract.exe" --tessdata-dir "C:\Program Files\Tesseract-OCR\tessdata" 
```

## XML to Arabic (character mapping)

```bash
python3 xml_to_arabic.py input.xml -o arabic.xml
```

## pdf to xml
```bash
 python3 pdf_to_xml.py "C:\Users\royassadi\Documents\Roya_Drive_C\Iranistik\Benedikt\Druz\main_sources\MPNP\wizidegiha-english-Tafazzoli&Ginoux .pdf" --ocr --lang fas --tesseract-cmd "C:\Program Files\Tesseract-OCR\tesseract.exe" --tessdata-dir "C:\Program Files\Tesseract-OCR\tessdata" --start 15 --end 85 -o DD1.xml
```

## Output format

```xml
<?xml version='1.0' encoding='utf-8'?>
<document>
  <url>...</url>
  <title>...</title>
  <text>
    <p>First paragraph...</p>
    <p>Second paragraph...</p>
  </text>
</document>
```

When using `--follow-next` or OCR, the output contains multiple pages:

```xml
<?xml version='1.0' encoding='utf-8'?>
<document>
  <page>
    <url>...</url>
    <title>...</title>
    <text>
      <p>...</p>
    </text>
  </page>
  <page>
    <image>...</image>
    <text>
      <p>...</p>
    </text>
  </page>
</document>
```

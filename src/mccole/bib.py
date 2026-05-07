"""Validate bibliography entries."""

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup
from markdown import markdown

from . import util


BIBLIOGRAPHY_PATH = Path("bibliography") / "index.md"
RE_DOI = re.compile(r"10\.\d{4,}/\S+")


def bib(options):
    """Validate bibliography entries."""
    bib_path = Path(options.src) / BIBLIOGRAPHY_PATH
    if not bib_path.exists():
        print(f"{bib_path}: not found", file=sys.stderr)
        return

    isbn_entries = []
    for key, hrefs in _parse_bibliography(bib_path):
        for href in hrefs:
            if "doi.org/" in href:
                _validate_doi(key, href)
            elif "/isbn/" in href:
                isbn = href.split("/isbn/", 1)[-1].strip("/")
                if _isbn_check_digit_valid(key, isbn):
                    isbn_entries.append((key, isbn))
    _validate_isbns_network(isbn_entries)


def _parse_bibliography(bib_path):
    """Convert bibliography Markdown to HTML and extract (key, [href, ...]) pairs."""
    md_text = bib_path.read_text(encoding="utf-8")
    html = markdown(md_text, extensions=util.MARKDOWN_EXTENSIONS)
    doc = BeautifulSoup(html, "html.parser")

    entries = []
    for dt in doc.find_all("dt"):
        span = dt.find("span", id=True)
        if span is None:
            continue
        key = span["id"]
        dd = dt.find_next_sibling("dd")
        if dd is None:
            continue
        hrefs = [a["href"] for a in dd.find_all("a", href=True)]
        entries.append((key, hrefs))
    return entries


def _validate_doi(key, href):
    """Validate DOI format and confirm it resolves via Crossref."""
    doi = href.split("doi.org/", 1)[-1]
    if not RE_DOI.fullmatch(doi):
        print(f"{key}: malformed DOI '{doi}'", file=sys.stderr)
        return
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='/')}"
    try:
        with urllib.request.urlopen(url) as resp:
            if resp.status != 200:
                print(f"{key}: DOI not found '{doi}'", file=sys.stderr)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            print(f"{key}: DOI not found '{doi}'", file=sys.stderr)
        else:
            print(f"{key}: DOI check failed (HTTP {exc.code}) '{doi}'", file=sys.stderr)
    except urllib.error.URLError as exc:
        print(f"{key}: DOI check failed ({exc.reason}) '{doi}'", file=sys.stderr)


def _isbn_check_digit_valid(key, isbn):
    """Validate ISBN-13 or ISBN-10 check digit. Print error and return False if invalid."""
    digits = isbn.replace("-", "").replace(" ", "")
    if len(digits) == 13:
        if not _isbn13_valid(digits):
            print(f"{key}: invalid ISBN-13 check digit '{isbn}'", file=sys.stderr)
            return False
    elif len(digits) == 10:
        if not _isbn10_valid(digits):
            print(f"{key}: invalid ISBN-10 check digit '{isbn}'", file=sys.stderr)
            return False
    else:
        print(f"{key}: malformed ISBN '{isbn}'", file=sys.stderr)
        return False
    return True


def _validate_isbns_network(isbn_entries):
    """Check all ISBNs against Open Library in a single batch request."""
    if not isbn_entries:
        return
    bibkeys = ",".join(f"ISBN:{isbn}" for _, isbn in isbn_entries)
    url = f"https://openlibrary.org/api/books?bibkeys={bibkeys}&format=json"
    try:
        with urllib.request.urlopen(url) as resp:
            found = set(json.loads(resp.read().decode("utf-8")))
    except urllib.error.URLError as exc:
        print(f"ISBN batch check failed ({exc.reason})", file=sys.stderr)
        return
    for key, isbn in isbn_entries:
        if f"ISBN:{isbn}" not in found:
            print(f"{key}: ISBN not found in Open Library '{isbn}'", file=sys.stderr)


def _isbn13_valid(digits):
    """Return True if the ISBN-13 check digit is correct."""
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits[:12]))
    return (10 - (total % 10)) % 10 == int(digits[12])


def _isbn10_valid(digits):
    """Return True if the ISBN-10 check digit is correct."""
    total = sum(int(d if d != "X" else 10) * (10 - i) for i, d in enumerate(digits))
    return total % 11 == 0

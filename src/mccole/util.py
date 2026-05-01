"""Utilities."""

from pathlib import Path
import sys

from bs4 import BeautifulSoup
from markdown import markdown


EXTRAS_DIR = Path("_extras")
LINKS_PATH = EXTRAS_DIR / "links.md"

HOME_PAGE = Path("README.md")

STANDARD_FILES = {
    "README.md": "",
    "CODE_OF_CONDUCT.md": "conduct",
    "CONTRIBUTING.md": "contributing",
    "LICENSE.md": "license",
}
REVERSE_FILES = {value: key for key, value in STANDARD_FILES.items() if value != ""}

MARKDOWN_EXTENSIONS = [
    "attr_list",
    "codehilite",
    "def_list",
    "fenced_code",
    "md_in_html",
    "tables",
]


def load_links(src_path):
    """Read links file if available."""
    links_path = src_path / LINKS_PATH
    return links_path.read_text(encoding="utf-8") if links_path.is_file() else ""


def load_order(src_path, home_page):
    """Determine section order from home page file."""
    md = (src_path / home_page).read_text(encoding="utf-8")
    html = markdown(md, extensions=MARKDOWN_EXTENSIONS)
    doc = BeautifulSoup(html, "html.parser")
    lessons = _load_order_section(doc, "lessons", lambda i: str(i + 1))
    appendices = _load_order_section(doc, "appendices", lambda i: chr(ord("A") + i))
    combined = {**lessons, **appendices}

    flattened = list(combined.keys())
    for i, slug in enumerate(flattened):
        combined[slug]["previous"] = flattened[i - 1] if i > 0 else None
        combined[slug]["next"] = flattened[i + 1] if i < (len(flattened) - 1) else None
        combined[slug]["filepath"] = src_path / REVERSE_FILES.get(
            slug, Path(slug) / "index.md"
        )

    return combined


def warn(message):
    print(message, file=sys.stderr)


def _get_slug_from_link(raw):
    """Convert '@/something/' to 'something'."""
    assert raw.startswith("@/") and raw.endswith("/")
    return raw[2:-1]


def _load_order_section(doc, selector, labeller):
    """Load a section of the table of contents from README.md DOM."""
    div = f"div#{selector}"
    return {
        _get_slug_from_link(node["href"]): {
            "number": labeller(i),
            "kind": selector,
            "title": node.decode_contents(),
        }
        for i, node in enumerate(doc.select(div)[0].select("a[href]"))
    }

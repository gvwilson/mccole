"""Utilities."""

from pathlib import Path
import sys


EXTRAS_DIR = Path("extras")
LINKS_PATH = EXTRAS_DIR / "links.md"


def load_links(src_path):
    """Read links file if available."""
    links_path = src_path / LINKS_PATH
    return links_path.read_text() if links_path.is_file() else ""


def warn(message):
    print(message, file=sys.stderr)

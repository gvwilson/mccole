"""Handle file inclusions with filtering."""

import re
from pathlib import Path
from bs4 import BeautifulSoup
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_for_filename, get_lexer_by_name
from pygments.util import ClassNotFound

from . import util


# Comment prefixes for different file types
COMMENT_FORMATS = {
    ".c": "//",
    ".cpp": "//",
    ".css": "//",
    ".html": "<!--",
    ".java": "//",
    ".js": "//",
    ".json": None,
    ".lua": "--",
    ".py": "#",
    ".r": "#",
    ".rs": "//",
    ".sh": "#",
    ".sql": "--",
    ".ts": "//",
    ".txt": "#",
    ".xml": "<!--",
}


def patch_inclusions(config, src_path, dst_path, doc):
    """Replace div elements with included file content."""
    for node in doc.select("div[data-inc]"):
        inc_file = node["data-inc"]
        mark = node.get("data-mark", "")
        omit = node.get("data-omit", "")
        head = node.get("data-head", "")
        scrub = node.get("data-scrub", "")
        try:
            filepath = src_path.parent / inc_file
            if not filepath.exists():
                raise FileNotFoundError(f"file {inc_file} not found")
            lines = filepath.read_text(encoding="utf-8").splitlines()
            if mark:
                lines = _filter_include(filepath, lines, mark)
            if omit:
                lines = _filter_exclude(filepath, lines, omit)
            if head:
                lines = _filter_head(lines, head)
            if scrub:
                lines = _filter_scrub(lines, scrub)
            content = "\n".join(lines)
            highlighted = _colorize_code(content, inc_file)
            soup = BeautifulSoup(highlighted, "html.parser")
            node.clear()
            node.append(soup)
        except Exception as exc:
            util.warn(f"unable to include {inc_file} in {dst_path}: {exc}")


def _colorize_code(content, filepath):
    """Colorize code using pygments based on file type."""
    try:
        lexer = get_lexer_for_filename(str(filepath))
    except ClassNotFound:
        lexer = get_lexer_by_name("text")
    
    formatter = HtmlFormatter(cssclass="codehilite", wrapcode=True,)
    return highlight(content, lexer, formatter)


def _filter_head(lines, n_str):
    """Keep the first N lines."""
    try:
        n = int(n_str)
        return lines[:n]
    except ValueError:
        raise ValueError(f"invalid head count: {n_str}")


def _filter_scrub(lines, pattern):
    """Remove substrings matching pattern from each line."""
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        raise ValueError(f"invalid scrub pattern '{pattern}': {exc}")
    return [compiled.sub("", line).rstrip() for line in lines]


def _filter_include(filepath, lines, marker):
    """Keep lines between mccole:marker comments."""
    if not re.match(r"^[\w-]+$", marker):
        raise ValueError(
            f"invalid marker (must be letters, digits, underscore, hyphen): {marker}"
        )

    comment_prefix = _get_comment_prefix(filepath)
    if comment_prefix is None:
        return lines[:]

    start_pattern = re.compile(
        rf"^\s*{re.escape(comment_prefix)}\s*mccole:\s*{re.escape(marker)}\s*$"
    )
    end_pattern = re.compile(
        rf"^\s*{re.escape(comment_prefix)}\s*mccole:\s*/{re.escape(marker)}\s*$"
    )

    result = []
    inside = False
    for line in lines:
        if start_pattern.match(line):
            inside = True
        elif end_pattern.match(line):
            break
        elif inside:
            result.append(line)

    # Strip leading and trailing blank lines
    while result and not result[0].strip():
        result.pop(0)
    while result and not result[-1].strip():
        result.pop()

    return result


def _filter_exclude(filepath, lines, marker):
    """Exclude lines between mccole:marker comments."""
    if not re.match(r"^[\w-]+$", marker):
        raise ValueError(
            f"invalid marker (must be letters, digits, underscore, hyphen): {marker}"
        )

    comment_prefix = _get_comment_prefix(filepath)
    start_pattern = re.compile(
        rf"^\s*{re.escape(comment_prefix)}\s*mccole:\s*{re.escape(marker)}\s*$"
    )

    result = []
    inside = False

    for line in lines:
        if start_pattern.match(line):
            inside = not inside
        elif not inside:
            result.append(line)

    # Strip leading and trailing blank lines
    while result and not result[0].strip():
        result.pop(0)
    while result and not result[-1].strip():
        result.pop()

    return result


def _get_comment_prefix(filepath):
    """Determine the comment prefix for a file based on its extension."""
    suffix = Path(filepath).suffix.lower()
    if suffix not in COMMENT_FORMATS:
        raise ValueError(f"unsupported file type: {suffix}")
    return COMMENT_FORMATS[suffix]

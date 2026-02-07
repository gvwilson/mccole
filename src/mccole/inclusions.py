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
        filters = node.get("data-filter", "")
        try:
            content = _include_file(config, src_path, inc_file, filters)
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


def _include_file(config, src_path, inc_file, filters):
    """Load and filter a file."""
    filepath = src_path.parent / inc_file
    if not filepath.exists():
        raise FileNotFoundError(f"file {inc_file} not found")

    content = filepath.read_text(encoding="utf-8")
    lines = content.splitlines()
    if filters:
        lines = _apply_filters(filepath, lines, filters)
    return "\n".join(lines)


def _apply_filters(filepath, lines, filter_spec):
    """Apply a series of filters to the lines."""

    # Split on '+' to get separate filter chains
    chains = [chain.strip() for chain in filter_spec.split("+") if chain.strip()]
    if not chains:
        return lines
    
    # Process each chain separately
    results = []
    for chain in chains:
        # Split on '|' for pipeline within this chain
        filters = [f.strip() for f in chain.split("|") if f.strip()]
        chain_result = lines
        for filter_str in filters:
            chain_result = _apply_single_filter(filepath, chain_result, filter_str)
        results.append(chain_result)
    
    # Join results with separator if multiple chains
    if len(results) == 1:
        return results[0]
    else:
        combined = []
        for i, result in enumerate(results):
            if i > 0:
                combined.append("...more...")
            combined.extend(result)
        return combined


def _apply_single_filter(filepath, lines, filter_str):
    """Apply a single filter to the lines."""
    if filter_str.count("=") != 1:
        raise ValueError(f"invalid filter format: {filter_str}")

    filter_type, filter_value = [f.strip() for f in filter_str.split("=")]

    if filter_type == "head":
        return _filter_head(lines, filter_value)
    elif filter_type == "tail":
        return _filter_tail(lines, filter_value)
    elif filter_type == "inc":
        return _filter_include(filepath, lines, filter_value)
    elif filter_type == "exc":
        return _filter_exclude(filepath, lines, filter_value)
    else:
        raise ValueError(f"unknown filter type: {filter_type}")


def _filter_head(lines, n_str):
    """Keep the first N lines."""
    try:
        n = int(n_str)
        return lines[:n]
    except ValueError:
        raise ValueError(f"invalid head count: {n_str}")


def _filter_tail(lines, n_str):
    """Keep the last N lines."""
    try:
        n = int(n_str)
        return lines[-n:] if n > 0 else []
    except ValueError:
        raise ValueError(f"invalid tail count: {n_str}")


def _filter_include(filepath, lines, marker):
    """Keep lines between mccole:marker comments."""
    if not re.match(r"^\w+$", marker):
        raise ValueError(
            f"invalid marker (must be letters, digits, underscore): {marker}"
        )

    comment_prefix = _get_comment_prefix(filepath)
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

    return result


def _filter_exclude(filepath, lines, marker):
    """Exclude lines between mccole:marker comments."""
    if not re.match(r"^\w+$", marker):
        raise ValueError(
            f"invalid marker (must be letters, digits, underscore): {marker}"
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

    return result


def _get_comment_prefix(filepath):
    """Determine the comment prefix for a file based on its extension."""
    suffix = Path(filepath).suffix.lower()
    if suffix not in COMMENT_FORMATS:
        raise ValueError(f"unsupported file type: {suffix}")
    return COMMENT_FORMATS[suffix]

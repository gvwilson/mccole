"""Handle file inclusions with filtering."""

import re
from pathlib import Path

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
            pre = doc.new_tag("pre")
            code = doc.new_tag("code")
            code.string = content
            pre.append(code)
            node.append(pre)
        except Exception as exc:
            util.warn(f"unable to include {inc_file} in {dst_path}: {exc}")


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
    filters = [f.strip() for f in filter_spec.split(";") if f.strip()]
    for filter_str in filters:
        lines = _apply_single_filter(filepath, lines, filter_str)
    return lines


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

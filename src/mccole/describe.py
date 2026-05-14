"""Describe contents of lesson files."""

import re
import shlex

from . import util
from .inclusions import (
    _filter_exclude,
    _filter_head,
    _filter_include,
    _filter_scrub,
)


# Same pattern used by shortcodes.py
_SHORTCODE_RE = re.compile(r"\[%\s*(/?[a-zA-Z_][a-zA-Z0-9_]*)(.*?)%\]", re.DOTALL)


def describe(options):
    """Describe contents of lesson files."""
    if options.inc:
        _describe_inclusions(options)


def _describe_inclusions(options):
    """Print a table of file inclusions found in lesson files."""
    order = util.load_order(options.src, options.root)
    rows = []

    for entry in order.values():
        src_path = entry["filepath"]
        if not src_path.exists():
            continue
        try:
            rel_including = str(src_path.relative_to(options.src))
        except ValueError:
            rel_including = str(src_path)

        content = src_path.read_text(encoding="utf-8")
        for inc_file, modifiers, line_count in _find_inclusions(src_path, content):
            inc_display = inc_file if not modifiers else f"{inc_file} ({modifiers})"
            rows.append((rel_including, inc_display, line_count))

    if not rows:
        return

    w0 = max(len("Lines"), max(len(str(r[2])) for r in rows))
    w1 = max(len("File"), max(len(r[0]) for r in rows))
    w2 = max(len("Included"), max(len(r[1]) for r in rows))

    fmt = f"{{:>{w0}}}  {{:<{w1}}}  {{:<{w2}}}"
    sep = "-" * w0 + "  " + "-" * w1 + "  " + "-" * w2
    print(fmt.format("Lines", "File", "Included"))
    print(sep)
    for including, included, lines in rows:
        print(fmt.format(lines, including, included))


def _find_inclusions(src_path, content):
    """Yield (inc_file, modifiers_str, line_count) for each [%inc%] in content."""
    for match in _SHORTCODE_RE.finditer(content):
        tag = match.group(1)
        if tag != "inc":
            continue

        args_str = match.group(2).strip()
        try:
            tokens = shlex.split(args_str)
        except ValueError:
            tokens = args_str.split()

        pargs = []
        kwargs = {}
        for token in tokens:
            if "=" in token:
                key, _, value = token.partition("=")
                kwargs[key.strip()] = value.strip().strip("'\"")
            else:
                pargs.append(token.strip("'\""))

        if "pat" in kwargs:
            pat = kwargs["pat"]
            for word in kwargs.get("fill", "").split():
                filename = pat.replace("*", word) if "*" in pat else pat
                filepath = src_path.parent / filename
                if filepath.exists():
                    lines, mods = _apply_filters(filepath, {})
                    yield filename, mods, len(lines)
        else:
            if not pargs:
                continue
            filename = pargs[0]
            filepath = src_path.parent / filename
            if not filepath.exists():
                continue
            lines, mods = _apply_filters(filepath, kwargs)
            yield filename, mods, len(lines)


def _apply_filters(filepath, kwargs):
    """Apply inclusion filters and return (lines, modifiers_str)."""
    lines = filepath.read_text(encoding="utf-8").splitlines()
    parts = []

    mark = kwargs.get("mark", "")
    omit = kwargs.get("omit", "")
    head = kwargs.get("head", "")
    scrub = kwargs.get("scrub", "")

    if mark:
        lines = _filter_include(filepath, lines, mark)
        parts.append(f"mark={mark}")
    if omit:
        lines = _filter_exclude(filepath, lines, omit)
        parts.append(f"omit={omit}")
    if head:
        lines = _filter_head(lines, head)
        parts.append(f"head={head}")
    if scrub:
        lines = _filter_scrub(lines, scrub)
        parts.append(f"scrub={scrub}")

    return lines, ", ".join(parts)

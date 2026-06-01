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
    if options.bibliography:
        _describe_bibliography(options)
    if options.glossary:
        _describe_glossary(options)
    if options.inc:
        _describe_inclusions(options)
    if options.words:
        _describe_words(options)


def _all_entries(options):
    """Return source file entries for lessons, appendices, and slides."""
    order = util.load_order(options.src, options.root)
    entries = list(order.values())
    for slide in util.load_slides(options.src):
        filepath = util.slides_src_file(options.src, slide["href"])
        entries.append({"filepath": filepath})
    return entries


def _describe_bibliography(options):
    """Print a table of bibliography keys and the files that reference them."""
    refs = {}  # {key: [file, ...]} in source order, deduplicated per file
    for entry in _all_entries(options):
        src_path = entry["filepath"]
        if not src_path.exists():
            continue
        try:
            label = str(src_path.relative_to(options.src))
        except ValueError:
            label = str(src_path)
        content = src_path.read_text(encoding="utf-8")
        seen_in_file = set()
        for match in _SHORTCODE_RE.finditer(content):
            if match.group(1) != "b":
                continue
            args_str = match.group(2).strip()
            try:
                tokens = shlex.split(args_str)
            except ValueError:
                tokens = args_str.split()
            for token in tokens:
                key = token.strip("'\"")
                if key and key not in seen_in_file:
                    seen_in_file.add(key)
                    refs.setdefault(key, []).append(label)

    if not refs:
        return

    w0 = max(len("Key"), max(len(k) for k in refs))
    w1 = max(len("Files"), max(len(", ".join(v)) for v in refs.values()))
    fmt = f"{{:<{w0}}}  {{:<{w1}}}"
    sep = "-" * w0 + "  " + "-" * w1
    print(fmt.format("Key", "Files"))
    print(sep)
    for key in sorted(refs):
        print(fmt.format(key, ", ".join(refs[key])))


def _describe_glossary(options):
    """Print a table of glossary keys and the files that reference them."""
    # Preserve README order for files; collect keys per file in that order
    refs = {}  # {key: [file, ...]} files in README order, deduplicated
    for entry in _all_entries(options):
        src_path = entry["filepath"]
        if not src_path.exists():
            continue
        try:
            label = str(src_path.relative_to(options.src))
        except ValueError:
            label = str(src_path)
        content = src_path.read_text(encoding="utf-8")
        seen_in_file = set()
        for match in _SHORTCODE_RE.finditer(content):
            if match.group(1) != "g":
                continue
            args_str = match.group(2).strip()
            try:
                tokens = shlex.split(args_str)
            except ValueError:
                tokens = args_str.split()
            if not tokens:
                continue
            key = tokens[0].strip("'\"")
            if key not in seen_in_file:
                seen_in_file.add(key)
                refs.setdefault(key, []).append(label)

    if not refs:
        return

    w0 = max(len("Key"), max(len(k) for k in refs))
    w1 = max(len("Files"), max(len(", ".join(v)) for v in refs.values()))
    fmt = f"{{:<{w0}}}  {{:<{w1}}}"
    sep = "-" * w0 + "  " + "-" * w1
    print(fmt.format("Key", "Files"))
    print(sep)
    for key in sorted(refs):
        print(fmt.format(key, ", ".join(refs[key])))


def _describe_inclusions(options):
    """Print a table of file inclusions found in lesson files."""
    rows = []

    for entry in _all_entries(options):
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


def _describe_words(options):
    """Print a table of word counts for each lesson and appendix index.md."""
    order = util.load_order(options.src, options.root)
    rows = []
    for slug, entry in order.items():
        src_path = entry["filepath"]
        if not src_path.exists():
            continue
        content = src_path.read_text(encoding="utf-8")
        rows.append((slug, len(content.split())))

    if not rows:
        return

    w0 = max(len("Slug"), max(len(r[0]) for r in rows))
    w1 = max(len("Words"), max(len(str(r[1])) for r in rows))
    fmt = f"{{:<{w0}}}  {{:>{w1}}}"
    sep = "-" * w0 + "  " + "-" * w1
    print(fmt.format("Slug", "Words"))
    print(sep)
    for slug, count in rows:
        print(fmt.format(slug, count))


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

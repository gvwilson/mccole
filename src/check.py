"""Check site."""

from collections import defaultdict
from pathlib import Path
import re
import sys

from bs4 import BeautifulSoup
from html5validator.validator import Validator

from . import util


GLOBAL = "<global>"
RE_FIGURE_CAPTION = re.compile(r"^Figure\s+\d+:")
RE_TABLE_CAPTION = re.compile(r"^Table\s+\d+:")


def check(options):
    """Check the site."""
    links = util.load_links(options.src)
    dst_dir = Path(options.dst)

    paths = [dst_dir / "index.html"] + list(dst_dir.glob("*/index.html"))
    pages = {fp: BeautifulSoup(fp.read_text(), "html.parser") for fp in paths}

    for func in [_check_all_html, _check_glossary_redefinitions,]:
        func(pages)

    for kind in ["bibliography", "glossary"]:
        _check_cross_references(options, pages, kind)

    for func in [
        _check_figure_structure,
        _check_single_h1,
        _check_table_structure,
        _check_unknown_links,
    ]:
        for path, doc in pages.items():
            func(options, path, doc)


def _check_all_html(pages):
    """Validate generated HTML."""
    validator = Validator()
    validator.validate(list(pages.keys()))


def _check_cross_references(options, pages, kind):
    """Check that all cross-references match entries."""
    known = _get_crossref_definitions(options, pages, kind)
    prefix = f"/{kind}/#"
    for path, doc in pages.items():
        for node in doc.select("a[href]"):
            if prefix not in node["href"]:
                continue
            key = node["href"].split("#")[-1]
            _require(path, key in known, f"unknown {kind} key {key}")


def _check_figure_structure(options, filepath, doc):
    """Check that all figures have IDs and captions."""
    for figure in doc.select("figure"):
        _require(filepath, "id" in figure.attrs, "figure missing 'id'")
        captions = figure.select("figcaption")
        if not _require(
            filepath, len(captions) == 1, "missing/extra figure caption(s)"
        ):
            return
        text = captions[0].string
        _require(
            filepath,
            RE_FIGURE_CAPTION.match(text),
            f"badly-formatted figure caption '{text}'",
        )


def _check_glossary_redefinitions(pages):
    """Check for glossary terms that are defined more than once."""
    seen = defaultdict(list)
    for path, doc in pages.items():
        for node in doc.select("a[href]"):
            if ("/glossary/#" in node["href"]) and (
                "term-defined" not in node.get("class", [])
            ):
                key = node["href"].split("#")[-1]
                seen[key].append(path)
    for key, values in seen.items():
        _require(
            GLOBAL,
            len(values) == 1,
            f"glossary entry '{key}' defined in {', '.join(sorted(str(v) for v in values))}",
        )


def _check_single_h1(options, filepath, doc):
    """Check that all pages have a single H1."""
    titles = doc.find_all("h1")
    _require(filepath, len(titles) == 1, f" {filepath} has {len(titles)} H1 elements")


def _check_table_structure(options, filepath, doc):
    """Check that all tables have proper structure and IDs."""
    for div in doc.select("div[data-caption]"):
        _require(filepath, "id" in div.attrs, "table missing 'id'")
        captions = div.select("caption")
        if not _require(filepath, len(captions) == 1, "missing/extra table caption(s)"):
            return
        text = captions[0].string
        _require(
            filepath,
            RE_TABLE_CAPTION.match(text),
            f"badly-formatted table caption '{text}'",
        )


def _check_unknown_links(options, filepath, doc):
    """Look for unresolved Markdown links."""
    unwanted = {"code", "pre"}
    for text in doc.find_all(string=lambda s: s and "][" in s):
        _require(
            filepath,
            any(p.name in unwanted for p in text.parents),
            f"possible unresolved Markdown link '{text}'",
        )


def _get_crossref_definitions(options, pages, kind):
    """Get set of known cross-reference keys."""
    path = Path(options.dst, kind, "index.html")
    if not _require(GLOBAL, path in pages, f"{kind} {path} not found"):
        return
    doc = pages[path]
    result = set()
    for outer in doc.find_all("dt"):
        inner = outer.find("span")
        result.add(inner.attrs["id"])
    return result


def _require(filepath, condition, message):
    """Manage warning messages."""
    if not condition:
        print(f"{filepath}: {message}", file=sys.stderr)
    return condition

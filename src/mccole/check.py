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
    dst_dir = Path(options.dst)

    paths = [dst_dir / "index.html"] + list(dst_dir.glob("*/index.html"))
    pages = {
        fp: BeautifulSoup(fp.read_text(encoding="utf-8"), "html.parser") for fp in paths
    }

    _check_tabs_in_markdown(options)

    _check_all_html(options, pages)
    _check_glossary_redefinitions(pages)

    _check_bibliography_alphabetical(options, pages)
    _check_bibliography_key_mismatch(options, pages)
    _check_bibliography_bare_isbns(options, pages)
    _check_glossary_alphabetical(options, pages)
    for kind in ["bibliography", "glossary"]:
        _check_cross_references(options, pages, kind)
        _check_unused_crossref_definitions(options, pages, kind)

    for func in [
        _check_figure_structure,
        _check_single_h1,
        _check_table_structure,
        _check_unknown_links,
    ]:
        for path, doc in pages.items():
            func(options, path, doc)


DIV_IN_SUMMARY = 'Element "div" not allowed as child of element "summary"'


def _check_all_html(options, pages):
    """Validate generated HTML."""
    ignore = [DIV_IN_SUMMARY] if options.relaxed else []
    validator = Validator(ignore=ignore)
    validator.validate(list(pages.keys()))


def _check_bibliography_alphabetical(options, pages):
    """Check that bibliography keys are in alphabetical order."""
    known = _get_crossref_definitions(options, pages, "bibliography")
    for i in range(1, len(known)):
        _require("bibliography", known[i] >= known[i-1], f"out-of-order key {known[i]}")


def _check_glossary_alphabetical(options, pages):
    """Check that glossary terms are in alphabetical order by lower-case term text."""
    terms = _get_glossary_term_texts(options, pages)
    for i in range(1, len(terms)):
        _require("glossary", terms[i].lower() >= terms[i-1].lower(), f"out-of-order term '{terms[i]}'")


def _check_cross_references(options, pages, kind):
    """Check that all cross-references match entries."""
    known = set(_get_crossref_definitions(options, pages, kind))
    prefix = f"/{kind}/#"
    for path, doc in pages.items():
        for node in doc.select("a[href]"):
            if prefix not in node["href"]:
                continue
            key = node["href"].split("#")[-1]
            _require(path, key in known, f"unknown {kind} key {key}")


def _check_element_structure(filepath, doc, selector, kind, caption_selector, pattern):
    """Check that figure-like elements have IDs and captions."""
    for node in doc.select(selector):
        if not _require(filepath, "id" in node.attrs, f"{kind} missing 'id'"):
            continue
        captions = node.select(caption_selector)
        if not _require(filepath, len(captions) == 1, f"missing/extra {kind} caption(s)"):
            continue
        text = captions[0].get_text()
        _require(filepath, pattern.match(text), f"badly-formatted {kind} caption '{text}'")


def _check_figure_structure(options, filepath, doc):
    """Check that all figures have IDs and captions."""
    _check_element_structure(
        filepath, doc, "figure", "figure", "figcaption", RE_FIGURE_CAPTION
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
    _check_element_structure(
        filepath, doc, "div[data-caption]", "table", "caption", RE_TABLE_CAPTION
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


def _check_tabs_in_markdown(options):
    """Report tab characters in Markdown source files."""
    order = util.load_order(options.src, options.root)
    md_paths = [options.src / options.root]
    md_paths.extend(entry["filepath"] for entry in order.values())
    for md_path in sorted(md_paths):
        for line_num, line in enumerate(md_path.read_text(encoding="utf-8").splitlines(), start=1):
            if "\t" in line:
                _require(f"{md_path}:{line_num}", False, "tab character in Markdown source")


def _get_glossary_term_texts(options, pages):
    """Get glossary term texts (not IDs) in document order."""
    path = Path(options.dst, "glossary", "index.html")
    if not _require(GLOBAL, path in pages, f"glossary {path} not found"):
        return []
    doc = pages[path]
    return [dt.get_text().strip() for dt in doc.find_all("dt")]


def _get_crossref_definitions(options, pages, kind):
    """Get set of known cross-reference keys."""
    path = Path(options.dst, kind, "index.html")
    if not _require(GLOBAL, path in pages, f"{kind} {path} not found"):
        return []
    doc = pages[path]
    return [outer.find("span").attrs["id"] for outer in doc.find_all("dt")]


def _get_crossref_usage(pages, kind):
    """Get the set of referenced keys for one cross-reference kind."""
    used = set()
    prefix = f"/{kind}/#"
    for doc in pages.values():
        for node in doc.select("a[href]"):
            href = node["href"]
            if prefix not in href:
                continue
            if (kind == "glossary") and ("term-defined" in node.get("class", [])):
                continue
            used.add(href.split("#")[-1])
    return used


def _check_bibliography_key_mismatch(options, pages):
    """Check that each bibliography span id matches its text content."""
    path = Path(options.dst, "bibliography", "index.html")
    if not _require(GLOBAL, path in pages, f"bibliography {path} not found"):
        return
    doc = pages[path]
    for dt in doc.find_all("dt"):
        span = dt.find("span", id=True)
        if span is None:
            continue
        span_id = span["id"]
        span_text = span.get_text().strip()
        _require("bibliography", span_id == span_text,
                 f"key mismatch: id='{span_id}' text='{span_text}'")


RE_BARE_ISBN = re.compile(r"\b97[89][-\d]{10,}\b|\b\d{9}[\dX]\b")


def _check_bibliography_bare_isbns(options, pages):
    """Warn about ISBN strings in bibliography definitions that are not hyperlinked."""
    path = Path(options.dst, "bibliography", "index.html")
    if path not in pages:
        return
    doc = pages[path]
    for dd in doc.find_all("dd"):
        bare_text = "".join(
            str(s) for s in dd.strings
            if not any(parent.name == "a" for parent in s.parents)
        )
        for match in RE_BARE_ISBN.finditer(bare_text):
            print(f"warning: bibliography: bare ISBN '{match.group()}'", file=sys.stderr)


def _check_unused_crossref_definitions(options, pages, kind):
    """Report defined cross-reference entries that are never referenced."""
    known = set(_get_crossref_definitions(options, pages, kind))
    used = _get_crossref_usage(pages, kind)
    for key in sorted(known - used):
        _require(GLOBAL, False, f"unused {kind} key {key}")


def _require(filepath, condition, message):
    """Manage warning messages."""
    if not condition:
        print(f"{filepath}: {message}", file=sys.stderr)
    return condition

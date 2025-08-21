"""Check generated HTML."""

import argparse
from collections import defaultdict
from pathlib import Path
import re
import sys

from bs4 import BeautifulSoup
from html5validator.validator import Validator

RE_FIGURE_CAPTION = re.compile(r"^Figure\s+\d+:")
RE_MD_CODE_PATTERNS = [
    re.compile(r"^```.+?^```", re.DOTALL + re.MULTILINE),
    re.compile(r"`.+?`", re.DOTALL + re.MULTILINE),
]
RE_MD_LINK_DEF = re.compile(r"^\[(.+?)\]:\s+.+?\s*$", re.MULTILINE)
RE_MD_LINK_REF = re.compile(r"\[.+?\]\[(.+?)\]", re.DOTALL | re.MULTILINE)


def main(opt):
    """Main driver."""
    opt._links = opt.links.read_text() if opt.links else None
    _check_markdown(opt)
    _check_html(opt)


def construct_parser(parser):
    """Parse command-line arguments."""
    parser.add_argument("--dst", type=Path, default="docs", help="output directory")
    parser.add_argument("--html", action="store_true", help="validate HTML")
    parser.add_argument("--links", type=Path, default=None, help="links file")
    parser.add_argument("--src", type=Path, default=".", help="source directory")


def _check_html(opt):
    """Check generated HTML."""
    html_paths = opt.dst.glob("**/*.html")
    html_pages = {
        path: BeautifulSoup(path.read_text(), "html.parser") for path in html_paths
    }
    for func in [
        _do_compare_readme_section_titles,
        _do_compare_template_readme,
        _do_exercise_titles,
        _do_figure_structure,
        _do_glossary_redefinitions,
        _do_single_h1,
        _do_table_structure,
        lambda o, p: _do_special_links(o, p, "bibliography"),
        lambda o, p: _do_special_links(o, p, "glossary"),
    ]:
        func(opt, html_pages)
    if opt.html:
        _do_html_validation(opt, html_pages)


def _check_markdown(opt):
    """Check source Markdown pages."""
    top_level = {path: path.read_text() for path in opt.src.glob("*.md")}
    sub_level = {path: path.read_text() for path in opt.src.glob("*/*.md")}
    markdown_pages = top_level | sub_level
    for func in [
        _do_unresolved_markdown_links,
    ]:
        func(opt, markdown_pages)


def _do_compare_readme_section_titles(opt, html_pages):
    """Make sure section titles in main page match those in sub-pages."""
    readme_path = opt.dst / "index.html"
    readme = BeautifulSoup(readme_path.read_text(), "html.parser")
    for kind, nav_selector in [
        ("lessons", "span#nav-lessons"),
        ("extras", "span#nav-extras"),
    ]:
        nav = readme.select(nav_selector)
        if not _require(
            len(nav) == 1, f"{readme_path} missing or multiple {nav_selector}"
        ):
            continue
        nav = nav[0]
        for node in nav.select("a"):
            expected = node.get_text()
            sub_path = opt.dst / node["href"] / "index.html"
            if not _require(
                sub_path in html_pages, f"README sub-path {sub_path} not found"
            ):
                continue
            actual = html_pages[sub_path].select("h1")
            if not _require(len(actual) == 1, f"missing/multiple H1 in {sub_path}"):
                continue
            actual = actual[0].get_text()
            _require(
                expected == actual,
                f"title mis-match between README {repr(expected)} and {sub_path} {repr(actual)}",
            )


def _do_compare_template_readme(opt, html_pages):
    """Compare tables of contents in template and README.md"""
    path = opt.dst / "index.html"
    readme = html_pages[path]
    for kind, nav_selector, body_selector in [
        ("lessons", "span#nav-lessons", "div#lessons"),
        ("extras", "span#nav-extras", "div#appendices"),
    ]:
        nav = readme.select(nav_selector)
        if not _require(len(nav) == 1, f"{path} missing or multiple {nav_selector}"):
            continue
        nav = nav[0]
        body = readme.select(body_selector)
        if not _require(len(body) == 1, f"{path} missing or multiple {body_selector}"):
            continue
        body = body[0]

        nav_entries = {node["href"]: node.string for node in nav.select("a[href]")}
        body_entries = {node["href"]: node.string for node in body.select("a[href]")}
        difference = set(nav_entries.keys()) ^ set(body_entries.keys())
        _require(
            not difference,
            f"mis-match in README and nav paths: {', '.join(sorted(difference))}",
        )

        common = set(nav_entries.keys()) & set(body_entries.keys())
        difference = [key for key in common if nav_entries[key] != body_entries[key]]
        _require(
            not difference,
            f"mis-match in README and nav paths text: {' '.join(sorted(difference))}",
        )


def _do_exercise_titles(opt, html_pages):
    """Check that exercise sections have one <h3> heading."""
    for path, doc in html_pages.items():
        for section in doc.select("section.exercise"):
            headings = section.select("h1, h2, h3, h4, h5, h6")
            _require(
                len(headings) == 1,
                f"exercise in {path} has missing/multiple heading(s)",
            )
            if len(headings) == 1:
                _require(
                    headings[0].name.lower() == "h3",
                    f"exercise in {path} has {headings[0].name} instead of h3",
                )


def _do_figure_structure(opt, html_pages):
    """Check that all figures have IDs and captions."""
    for path, doc in html_pages.items():
        for figure in doc.select("figure"):
            _require("id" in figure.attrs, f"figure missing 'id' in {path}")
            captions = figure.select("figcaption")
            if not _require(
                len(captions) == 1, f"figure missing/extra caption in {path}"
            ):
                continue
            text = captions[0].string
            _require(
                RE_FIGURE_CAPTION.match(text),
                f"badly-formatted figure caption '{text}' in {path}",
            )


def _do_glossary_redefinitions(opt, html_pages):
    """Check for glossary terms that are defined more than once."""
    seen = defaultdict(list)
    for path, doc in html_pages.items():
        for node in doc.select("a[href]"):
            if "/glossary/#" in node["href"]:
                key = node["href"].split("#")[-1]
                seen[key].append(path)
    for key, values in seen.items():
        _require(
            len(values) == 1,
            f"glossary entry '{key}' defined in {', '.join(sorted(str(v) for v in values))}",
        )


def _do_html_validation(opt, html_pages):
    """Validate generated HTML."""
    validator = Validator()
    errors = validator.validate(list(html_pages.keys()))


def _do_single_h1(opt, html_pages):
    """Check that each page has exactly one <h1>."""
    for path, doc in html_pages.items():
        titles = doc.find_all("h1")
        _require(len(titles) == 1, f"{len(titles)} H1 elements found in {path}")


def _do_special_links(opt, html_pages, stem):
    """Check specially-formatted links."""
    source = opt.dst / stem / "index.html"
    if not _require(source in html_pages, f"{source} not found"):
        return

    main = html_pages[source].select("main")
    if not _require(len(main) == 1, f"missing or multiple <main> in {source}"):
        return

    main = main[0]
    defined = {node["id"] for node in main.select("span") if node.has_attr("id")}

    base = f"{stem}/#"
    used = set()
    for path, doc in html_pages.items():
        here = {
            node["href"].split("#")[-1]
            for node in doc.select("a[href]")
            if base in node["href"]
        }
        used |= here
        unknown = here - defined
        _require(
            len(unknown) == 0,
            f"unknown {stem} keys in {path}: {', '.join(sorted(unknown))}",
        )

    unused = defined - used
    _require(len(unused) == 0, f"unused {stem} keys: {', '.join(sorted(unused))}")


def _do_table_structure(opt, html_pages):
    """Check that all tables have proper structure and IDs."""
    for path, doc in html_pages.items():
        table_divs = doc.select("div[data-table-id], div[data-table-caption]")
        for div in table_divs:
            if not _require(
                "data-table-id" in div.attrs,
                f"table div missing 'data-table-id' in {path}",
            ):
                continue
            table_id = div["data-table-id"]
            _require(
                table_id.startswith("t:"),
                f"table ID '{table_id}' does not start with 't:' in {path}",
            )
            _require(
                "data-table-caption" in div.attrs,
                f"table div missing 'data-table-caption' in {path}",
            )
            tables = div.select("table")
            _require(
                len(tables) == 1,
                f"table div should contain exactly one table, found {len(tables)} in {path}",
            )


def _do_unresolved_markdown_links(opt, markdown_pages):
    """Check for [text][key] that doesn't resolve and for unused link definitions."""
    general = (
        set()
        if opt._links is None
        else set(m for m in RE_MD_LINK_DEF.findall(opt._links))
    )
    seen = set()
    for path, md in markdown_pages.items():
        for pat in RE_MD_CODE_PATTERNS:
            md = pat.sub("", md)
        referenced = set(m for m in RE_MD_LINK_REF.findall(md))
        in_page = set(m for m in RE_MD_LINK_DEF.findall(md))

        unknown = (referenced - in_page) - general
        _require(
            not unknown,
            f"undefined link reference(s) in {path}: {', '.join(sorted(unknown))}",
        )

        unused = in_page - referenced
        _require(
            not unused,
            f"unused link definition(s) in {path}: {', '.join(sorted(unused))}",
        )

        seen |= referenced & general

    unused = general - seen
    _require(
        not unused, f"unused global link definition(s): {', '.join(sorted(unused))}"
    )


def _require(cond, msg):
    """Check and report."""
    if not cond:
        print(msg, file=sys.stderr)
    return cond

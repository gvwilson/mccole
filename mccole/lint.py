"""Check generated HTML."""

import argparse
from collections import defaultdict
from pathlib import Path
import sys

from bs4 import BeautifulSoup
from html5validator.validator import Validator


def lint(opt):
    """Main driver."""
    filepaths = Path(opt.dst).glob("**/*.html")
    pages = {path: BeautifulSoup(path.read_text(), "html.parser") for path in filepaths}
    for func in [
        _do_compare_template_readme,
        _do_exercise_titles,
        _do_glossary_redefinitions,
        _do_single_h1,
        lambda o, p: _do_special_links(o, p, "bibliography"),
        lambda o, p: _do_special_links(o, p, "glossary"),
    ]:
        func(opt, pages)
    if opt.html:
        _do_html_validation(opt, pages)


def construct_parser(parser):
    """Parse command-line arguments."""
    parser.add_argument("--dst", type=Path, default="docs", help="output directory")
    parser.add_argument("--html", action="store_true", help="validate HTML")


def _do_compare_template_readme(opt, pages):
    """Compare tables of contents in template and README.md"""
    path = opt.dst / "index.html"
    readme = pages[path]
    for (kind, nav_selector, body_selector) in [
        ("lessons", "span#nav-lessons", "div#syllabus"),
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

        nav_paths = {node["href"] for node in nav.select("a[href]")}
        body_paths = {node["href"] for node in body.select("a[href]")}
        difference = nav_paths ^ body_paths
        _require(not difference, f"mis-match in README and nav paths: {', '.join(sorted(difference))}")


def _do_exercise_titles(opt, pages):
    """Check that exercise sections have one <h3> heading."""
    for path, doc in pages.items():
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


def _do_glossary_redefinitions(opt, pages):
    """Check for glossary terms that are defined more than once."""
    seen = defaultdict(list)
    for path, doc in pages.items():
        for node in doc.select("a[href]"):
            if "/glossary/#" in node["href"]:
                key = node["href"].split("#")[-1]
                seen[key].append(path)
    for key, values in seen.items():
        _require(
            len(values) == 1,
            f"glossary entry '{key}' defined in {', '.join(sorted(str(v) for v in values))}",
        )


def _do_html_validation(opt, pages):
    """Validate generated HTML."""
    validator = Validator()
    errors = validator.validate(list(pages.keys()))


def _do_single_h1(opt, pages):
    """Check that each page has exactly one <h1>."""
    for path, doc in pages.items():
        titles = doc.find_all("h1")
        _require(len(titles) == 1, f"{len(titles)} H1 elements found in {path}")


def _do_special_links(opt, pages, stem):
    """Check specially-formatted links."""
    source = opt.dst / stem / "index.html"
    if not _require(source in pages, f"{source} not found"):
        return

    main = pages[source].select("main")
    if not _require(len(main) == 1, f"missing or multiple <main> in {source}"):
        return

    main = main[0]
    defined = {
        node["id"] for node in main.select("span") if node.has_attr("id")
    }

    base = f"{stem}/#"
    used = set()
    for path, doc in pages.items():
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


def _require(cond, msg):
    """Check and report."""
    if not cond:
        print(msg, file=sys.stderr)
    return cond

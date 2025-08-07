"""Check generated HTML."""

import argparse
from collections import defaultdict
from pathlib import Path
import sys

from bs4 import BeautifulSoup


def lint(opt):
    """Main driver."""
    filepaths = Path(opt.dst).glob("**/*.html")
    pages = {path: BeautifulSoup(path.read_text(), "html.parser") for path in filepaths}
    for func in [
        _do_exercise_titles,
        _do_glossary_redefinitions,
        _do_single_h1,
        lambda o, p: _do_special_links(o, p, "bibliography"),
        lambda o, p: _do_special_links(o, p, "glossary"),
    ]:
        func(opt, pages)


def construct_parser(parser):
    """Parse command-line arguments."""
    parser.add_argument("--dst", type=Path, default="docs", help="output directory")


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

    defined = {
        node["id"] for node in pages[source].select("span") if node.has_attr("id")
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

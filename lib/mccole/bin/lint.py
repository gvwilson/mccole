"""Check project."""

import argparse
import ark
from bs4 import BeautifulSoup, Tag
from pathlib import Path
import re
import shortcodes


def main():
    options = parse_args()
    found = collect_actual(options)
    for f in [
        bib_check,
    ]:
        f(options, found)


def bib_check(options, found):
    """Check bibliography citations."""
    expected = bib_get_keys(options)
    for key, slugs in found["bib"].items():
        if key not in expected:
            print(f"unknown bib key {key} used in {listify(slugs)}")
        else:
            expected.remove(key)
    if expected:
        print(f"unused bib keys {listify(expected)}")


def bib_get_keys(options):
    """Get actual bibliography keys."""
    text = Path(options.root, "info", "bibliography.bib").read_text()
    return re.findall(r"^@.+?\{(.+?),$", text, re.MULTILINE)


def collect_actual(options):
    """Collect values from files."""
    parser = shortcodes.Parser(inherit_globals=False, ignore_unknown=True)
    parser.register(_collect_bib, "b")
    collected = {
        "bib": {},
    }
    ark.nodes.root().walk(
        lambda node: _collect_visitor(node, parser, collected)
    )
    return collected


def _collect_bib(pargs, kwargs, found):
    """Collect data from a bibliography reference shortcode."""
    found["bib"].update(pargs)


def _collect_visitor(node, parser, collected):
    """Visit each node, collecting data."""
    found = {
        "bib": set(),
    }
    parser.parse(node.text, found)
    for key in found["bib"]:
        if key not in collected["bib"]:
            collected["bib"][key] = set()
        collected["bib"][key].add(node.slug)


def listify(values):
    """Format values for printing."""
    return ", ".join(sorted(list(values)))


def parse_args():
    """Parse arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--dom", required=True, help="DOM specification file")
    parser.add_argument("--pages", nargs="+", default=[], help="pages")
    parser.add_argument("--root", required=True, help="Root directory")
    return parser.parse_args()


if __name__ == "__main__":
    main()

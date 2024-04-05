"""Check project."""

import argparse
import ark
from bs4 import BeautifulSoup, Tag
from pathlib import Path
import re
import shortcodes
import yaml


def main():
    options = parse_args()
    found = collect_actual(options)
    for func in [
        bib_check,
        glossary_check,
    ]:
        func(options, found)


def bib_check(options, found):
    """Check bibliography citations."""
    expected = bib_get_keys(options)
    check_keys("bibliography", expected, found["bib"])


def bib_get_keys(options):
    """Get actual bibliography keys."""
    text = Path(options.root, "info", "bibliography.bib").read_text()
    return set(re.findall(r"^@.+?\{(.+?),$", text, re.MULTILINE))


def check_keys(kind, expected, actual):
    """Check two sets of keys."""
    for key, slugs in actual.items():
        if key not in expected:
            print(f"unknown {kind} key {key} used in {listify(slugs)}")
        else:
            expected.remove(key)
    if expected:
        print(f"unused {kind} keys {listify(expected)}")


def collect_actual(options):
    """Collect values from files."""
    parser = shortcodes.Parser(inherit_globals=False, ignore_unknown=True)
    parser.register(collect_bib, "b")
    parser.register(collect_glossary, "g")
    collected = {
        "bib": {},
        "glossary": {},
    }
    ark.nodes.root().walk(
        lambda node: collect_visitor(node, parser, collected)
    )
    return collected


def collect_bib(pargs, kwargs, found):
    """Collect data from a bibliography reference shortcode."""
    found["bib"].update(pargs)


def collect_glossary(pargs, kwargs, found):
    """Collect data from a glossary reference shortcode."""
    found["glossary"].add(pargs[0])


def collect_visitor(node, parser, collected):
    """Visit each node, collecting data."""
    found = {
        "bib": set(),
        "glossary": set(),
    }
    parser.parse(node.text, found)
    for kind in ("bib", "glossary"):
        reorganize_found(node, kind, collected, found)


def reorganize_found(node, kind, collected, found):
    """Copy found keys into overall collection."""
    for key in found[kind]:
        if key not in collected[kind]:
            collected[kind][key] = set()
        collected[kind][key].add(node.slug)


def glossary_get_keys(options):
    """Get actual glossary keys."""
    text = Path(options.root, "info", "glossary.yml").read_text()
    glossary = yaml.safe_load(text) or []
    if isinstance(glossary, dict):
        glossary = [glossary]
    return {entry["key"] for entry in glossary}


def glossary_check(options, found):
    """Check glossary citations."""
    expected = glossary_get_keys(options)
    check_keys("glossary", expected, found["glossary"])


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

"""Check project."""

import argparse
import ark
from pathlib import Path
import re
import shortcodes
import yaml


def main():
    options = parse_args()
    found = collect_actual(options)
    for func in [
        check_bib,
        check_fig,
        check_gloss,
    ]:
        func(options, found)


def check_bib(options, found):
    """Check bibliography citations."""
    expected = get_bib_keys(options)
    check_keys("bibliography", expected, found["bib"])


def check_fig(options, found):
    """Check figure definitions and citations."""
    check_keys("figure", set(found["fig_def"].keys()), found["fig_ref"])


def check_gloss(options, found):
    """Check glossary citations."""
    expected = get_gloss_keys(options)
    check_keys("gloss", expected, found["gloss"])


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
    parser.register(collect_fig_def, "figure")
    parser.register(collect_fig_ref, "f")
    parser.register(collect_gloss, "g")
    collected = {
        "bib": {},
        "fig_def": {},
        "fig_ref": {},
        "gloss": {},
    }
    ark.nodes.root().walk(
        lambda node: collect_visitor(node, parser, collected)
    )
    return collected


def collect_bib(pargs, kwargs, found):
    """Collect data from a bibliography reference shortcode."""
    found["bib"].update(pargs)


def collect_fig_def(pargs, kwargs, found):
    """Collect data from a figure definition shortcode."""
    slug = kwargs["slug"]
    if slug in found["fig_def"]:
        print("Duplicate definition of figure slug {slug}")
    else:
        found["fig_def"].add(slug)


def collect_fig_ref(pargs, kwargs, found):
    """Collect data from a figure reference shortcode."""
    found["fig_ref"].add(pargs[0])


def collect_gloss(pargs, kwargs, found):
    """Collect data from a glossary reference shortcode."""
    found["gloss"].add(pargs[0])


def collect_visitor(node, parser, collected):
    """Visit each node, collecting data."""
    found = {
        "bib": set(),
        "fig_def": set(),
        "fig_ref": set(),
        "gloss": set(),
    }
    parser.parse(node.text, found)
    for kind in found:
        reorganize_found(node, kind, collected, found)


def get_bib_keys(options):
    """Get actual bibliography keys."""
    text = Path(options.root, "info", "bibliography.bib").read_text()
    return set(re.findall(r"^@.+?\{(.+?),$", text, re.MULTILINE))


def get_gloss_keys(options):
    """Get actual glossary keys."""
    text = Path(options.root, "info", "glossary.yml").read_text()
    glossary = yaml.safe_load(text) or []
    if isinstance(glossary, dict):
        glossary = [glossary]
    return {entry["key"] for entry in glossary}


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


def reorganize_found(node, kind, collected, found):
    """Copy found keys into overall collection."""
    for key in found[kind]:
        if key not in collected[kind]:
            collected[kind][key] = set()
        collected[kind][key].add(node.slug)


if __name__ == "__main__":
    main()

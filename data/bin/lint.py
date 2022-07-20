#!/usr/bin/env python

"""Check project."""


import argparse
import re
from pathlib import Path

import utils
from bs4 import BeautifulSoup, Tag

INDEX_FILE = "index.md"
RE_FILE = re.compile(r'\[%\s+excerpt.+?f="(.+?)".+?%\]')
RE_PAT = re.compile(r'\[%\s+excerpt.+?pat="(.+?)"\s+fill="(.+?)".+?%\]')


def main():
    """Main driver."""
    options = parse_args()

    source_files = get_src(options)
    check_excerpts(source_files)

    html_files = get_html(options)
    check_dom(options.dom, html_files)


def check_dom(dom_spec, html_files):
    """Check DOM elements in generated files."""
    allowed = utils.read_yaml(dom_spec)
    seen = {}
    for filename in html_files:
        with open(filename, "r") as reader:
            _collect_dom(seen, BeautifulSoup(reader.read(), "html.parser"))
    _diff_dom("extra", seen, allowed)


def check_excerpts(source_files):
    """Check for excerpted files."""
    for (dirname, filename) in source_files:
        referenced = get_excerpts(Path(dirname, filename))
        existing = get_files(dirname)
        report(dirname, "excerpts", referenced, existing)


def get_excerpts(filename):
    """Find excerpt filenames."""
    with open(filename, "r") as reader:
        text = reader.read()
        result = {m.group(1) for m in RE_FILE.finditer(text)}
        pats = [(m.group(1), m.group(2)) for m in RE_PAT.finditer(text)]
        for (pat, fill) in pats:
            result |= {pat.replace("*", f) for f in fill.split()}
        return result


def get_files(dirname):
    """Return set of files."""
    return set(
        f.name
        for f in Path(dirname).iterdir()
        if f.is_file() and (f.name != INDEX_FILE)
    )


def get_html(options):
    """Get paths to HTML files for processing."""
    return list(Path(options.html).glob("**/*.html"))


def get_src(options):
    """Get (file, dir) pairs for processing."""
    result = [(options.src, INDEX_FILE)]
    subdirs = [s for s in Path(options.src).iterdir() if s.is_dir()]
    return result + [(s, INDEX_FILE) for s in subdirs]


def parse_args():
    """Parse arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--dom", required=True, help="YAML spec of allowed DOM")
    parser.add_argument("--html", required=True, help="HTML directory")
    parser.add_argument("--src", required=True, help="Source directory")
    return parser.parse_args()


def report(dirname, title, expected, actual):
    """Report problems."""
    if expected == actual:
        return
    print(f"{dirname}: {title}")
    for (subtitle, items) in [
        ("missing", expected - actual),
        ("extra", actual - expected),
    ]:
        if not items:
            continue
        print(f"- {subtitle}")
        for i in sorted(items):
            print(f"  - {i}")


def _collect_dom(seen, node):
    """Collect DOM element attributes from given node and its descendents."""
    if not isinstance(node, Tag):
        return
    if node.name not in seen:
        seen[node.name] = {}
    for (key, value) in node.attrs.items():
        if key not in seen[node.name]:
            seen[node.name][key] = set()
        if isinstance(value, str):
            seen[node.name][key].add(value)
        else:
            for v in value:
                seen[node.name][key].add(v)
    for child in node:
        _collect_dom(seen, child)


def _diff_dom(title, left, right):
    """Show difference between two DOM structures."""
    for name in sorted(left):
        if name not in right:
            print(f"{title}: {name} seen but not expected")
            continue
        for attr in sorted(left[name]):
            if attr not in right[name]:
                print(f"{title}: {name}.{attr} seen but not expected")
                continue
            if right[name][attr] is None:
                continue
            for value in sorted(left[name][attr]):
                if value not in right[name][attr]:
                    print(f"{title}: {name}.{attr} == '{value}' seen but not expected")


if __name__ == "__main__":
    main()

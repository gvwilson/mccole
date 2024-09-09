"""Check site consistency."""

import argparse
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
import re

from .util import MD_LINK_DEF, SUFFIXES, SUFFIXES_SRC, find_files, find_key_defs, load_config


BIB_REF = re.compile(r"\[.+?\]\(b:(.+?)\)", re.MULTILINE)
FIGURE_DEF = re.compile(r'<figure\s+id="(.+?)"\s*>', re.MULTILINE)
FIGURE_REF = re.compile(r"\[[^\]]+?\]\(f:(.+?)\)", re.MULTILINE)
GLOSS_REF = re.compile(r"\[[^\]]+?\]\(g:(.+?)\)", re.MULTILINE)
MD_CODEBLOCK_FILE = re.compile(r"^```\s*\{\s*\.(.+?)\s+\#(.+?)\s*\}\s*$(.+?)^```\s*$", re.DOTALL + re.MULTILINE)
MD_FILE_LINK = re.compile(r"\[(.+?)\]\((.+?)\)", re.MULTILINE)
MD_LINK_REF = re.compile(r"\[(.+?)\]\[(.+?)\]", re.MULTILINE)
TABLE_DEF = re.compile(r'<table\s+id="(.+?)"\s*>', re.MULTILINE)
TABLE_REF = re.compile(r"\[[^\]]+?\]\(t:(.+?)\)", re.MULTILINE)


def lint(opt):
    """Main driver."""
    config = load_config(opt.config)
    files = find_files(opt, {opt.out})

    check_duplicates(files, config["duplicates"])
    check_file_references(files)

    sections = {
        filepath: content
        for filepath, content in files.items()
        if filepath.suffix == ".md"
    }
    linters = [
        lint_bibliography_references,
        lint_codeblock_inclusions,
        lint_figure_references,
        lint_glossary_redefinitions,
        lint_glossary_references,
        lint_link_definitions,
        lint_markdown_links,
        lint_table_references,
    ]
    if all(list(f(opt, sections) for f in linters)):
        print("All self-checks passed.")


def check_duplicates(files, expected):
    """Confirm that duplicated files are as expected."""

    # Construct groups of duplicated files
    actual = defaultdict(set)
    for filepath, content in files.items():
        if filepath.suffix not in SUFFIXES_SRC:
            continue
        hash_code = sha256(bytes(content, "utf-8")).hexdigest()
        actual[hash_code].add(str(filepath))
    actual = set(frozenset(grp) for grp in actual.values() if len(grp) > 1)

    # Report groups
    differences = actual.symmetric_difference(expected)
    if differences:
        print("duplicate mismatch")
        for d in differences:
            print(f"- {', '.join(sorted(d))}")


def check_file_references(files):
    """Check inter-file references."""
    ok = True
    for filepath, content in files.items():
        if filepath.suffix != ".md":
            continue
        for link in MD_FILE_LINK.finditer(content):
            if _is_special_link(link.group(2)):
                continue
            target = _resolve_path(filepath.parent, link.group(2))
            if _is_missing(target, files):
                print(f"Missing file: {filepath} => {target}")
                ok = False
    return ok


def lint_bibliography_references(opt, sections):
    """Check bibliography references."""
    available = find_key_defs(sections, "bibliography")
    if available is None:
        print("No bibliography found (or multiple matches)")
        return False
    return _check_references(sections, "bibliography", BIB_REF, available)


def lint_codeblock_inclusions(opt, sections):
    """Check file inclusions."""
    ok = True
    for filepath, content in sections.items():
        for block in MD_CODEBLOCK_FILE.finditer(content):
            codepath, expected = block.group(2), block.group(3).strip()
            actual = Path(filepath.parent, codepath).read_text().strip()
            if actual != expected:
                print(f"Content mismatch: {filepath} => {codepath}")
                ok = False
    return ok


def lint_figure_references(opt, sections):
    """Check figure references."""
    return _check_object_refs(sections, "figure", FIGURE_DEF, FIGURE_REF)


def lint_glossary_redefinitions(opt, sections):
    """Check glossary redefinitions."""
    found = defaultdict(set)
    for filepath, content in sections.items():
        if "glossary" in str(filepath).lower():
            continue
        for m in GLOSS_REF.finditer(content):
            found[m[1]].add(str(filepath))

    problems = {k:v for k, v in found.items() if len(v) > 1}
    for k, v in problems.items():
        if len(v) > 1:
            print(f"glossary key {k} redefined: {', '.join(sorted(v))}")
    return len(problems) == 0


def lint_glossary_references(opt, sections):
    """Check glossary references."""
    available = find_key_defs(sections, "glossary")
    if available is None:
        print("No glossary found (or multiple matches)")
        return False
    return _check_references(sections, "glossary", GLOSS_REF, available)


def lint_link_definitions(opt, sections):
    """Check that Markdown files define the links they use."""
    ok = True
    for filepath, content in sections.items():
        link_refs = {m[1] for m in MD_LINK_REF.findall(content)}
        link_defs = {m[0] for m in MD_LINK_DEF.findall(content)}
        ok = ok and _report_diff(f"{filepath} links", link_refs, link_defs)
    return ok


def lint_markdown_links(opt, sections):
    """Check consistency of Markdown links."""
    found = defaultdict(lambda: defaultdict(set))
    for filepath, content in sections.items():
        for link in MD_LINK_DEF.finditer(content):
            label, url = link.group(1), link.group(2)
            found[label][url].add(filepath)

    ok = True
    for label, data in found.items():
        if len(data) > 1:
            print(f"Inconsistent link: {label} => {data}")
            ok = False
    return ok


def lint_table_references(opt, sections):
    """Check figure references."""
    return _check_object_refs(sections, "table", TABLE_DEF, TABLE_REF)


def parse_args(parser):
    """Parse command-line arguments."""
    parser.add_argument("--config", type=str, default="pyproject.toml", help="optional configuration file")
    parser.add_argument("--out", type=str, default="docs", help="output directory")
    parser.add_argument("--root", type=str, default=".", help="root directory")
    return parser


def _check_object_refs(sections, kind, pattern_def, pattern_ref):
    """Check for figure and table references within each Markdown file."""
    ok = True
    for filepath, content in sections.items():
        defined = set(pattern_def.findall(content))
        referenced = set(pattern_def.findall(content))
        ok = _report_diff(f"{filepath} {kind}", referenced, defined) and ok
    return ok


def _check_references(sections, term, regexp, available):
    """Check all Markdown files for cross-references."""
    ok = True
    seen = set()
    for filepath, content in sections.items():
        found = {k.group(1) for k in regexp.finditer(content)}
        seen |= found
        missing = found - available
        if missing:
            print(f"Missing {term} keys in {filepath}: {', '.join(sorted(missing))}")
            ok = False

    unused = available - seen
    if unused:
        print(f"Unused {term} keys: {', '.join(sorted(unused))}")
        ok = False

    return ok


def _is_missing(actual, available):
    """Is a file missing?"""
    return (not actual.exists()) or (
        (actual.suffix in SUFFIXES) and (actual not in available)
    )


def _is_special_link(link):
    """Is this link handled specially?"""
    return link.startswith("b:") or link.startswith("g:")


def _report_diff(msg, refs, defs):
    """Report differences if any."""
    ok = True
    for (kind, vals) in (("missing", refs - defs), ("unused", defs - refs)):
        if vals:
            print(f"{msg} {kind}: {', '.join(vals)}")
            ok = False
    return ok


def _resolve_path(source, dest):
    """Account for '..' in paths."""
    while dest[:3] == "../":
        source = source.parent
        dest = dest[3:]
    result = Path(source, dest)
    return result


if __name__ == "__main__":
    opt = parse_args(argparse.ArgumentParser()).parse_args()
    lint(opt)

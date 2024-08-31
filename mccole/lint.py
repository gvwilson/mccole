"""Check site consistency."""

import argparse
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
import re

from .util import MD_LINK_DEF, SUFFIXES, SUFFIXES_SRC, find_files, find_key_defs, load_config


BIB_REF = re.compile(r"\[.+?\]\(b:(.+?)\)", re.MULTILINE)
GLOSS_REF = re.compile(r"\[[^\]]+?\]\(g:(.+?)\)", re.MULTILINE)
MD_CODEBLOCK_FILE = re.compile(r"^```\s*\{\s*\.(.+?)\s+\#(.+?)\s*\}\s*$(.+?)^```\s*$", re.DOTALL + re.MULTILINE)
MD_FILE_LINK = re.compile(r"\[(.+?)\]\((.+?)\)", re.MULTILINE)
MD_LINK_REF = re.compile(r"\[(.+?)\]\[(.+?)\]", re.MULTILINE)


def lint(opt):
    """Main driver."""
    config = load_config(opt.config)
    files = find_files(opt, {opt.out})
    check_duplicates(files, config["duplicates"])
    linters = [
        lint_bibliography_references,
        lint_codeblock_files,
        lint_file_references,
        lint_glossary_redefinitions,
        lint_glossary_references,
        lint_link_definitions,
        lint_markdown_links,
    ]
    if all(list(f(opt, files) for f in linters)):
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


def check_references(files, term, regexp, available):
    """Check all files for cross-references."""
    ok = True
    seen = set()
    for filepath, content in files.items():
        if filepath.suffix != ".md":
            continue
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


def is_missing(actual, available):
    """Is a file missing?"""
    return (not actual.exists()) or (
        (actual.suffix in SUFFIXES) and (actual not in available)
    )


def is_special_link(link):
    """Is this link handled specially?"""
    return link.startswith("b:") or link.startswith("g:")


def lint_bibliography_references(opt, files):
    """Check bibliography references."""
    available = find_key_defs(files, "bibliography")
    if available is None:
        print("No bibliography found (or multiple matches)")
        return False
    return check_references(files, "bibliography", BIB_REF, available)


def lint_codeblock_files(opt, files):
    """Check file inclusions."""
    ok = True
    for filepath, content in files.items():
        if filepath.suffix != ".md":
            continue
        for block in MD_CODEBLOCK_FILE.finditer(content):
            codepath, expected = block.group(2), block.group(3).strip()
            actual = Path(filepath.parent, codepath).read_text().strip()
            if actual != expected:
                print(f"Content mismatch: {filepath} => {codepath}")
                ok = False
    return ok


def lint_file_references(opt, files):
    """Check inter-file references."""
    ok = True
    for filepath, content in files.items():
        if filepath.suffix != ".md":
            continue
        for link in MD_FILE_LINK.finditer(content):
            if is_special_link(link.group(2)):
                continue
            target = resolve_path(filepath.parent, link.group(2))
            if is_missing(target, files):
                print(f"Missing file: {filepath} => {target}")
                ok = False
    return ok


def lint_glossary_redefinitions(opt, files):
    """Check glossary redefinitions."""
    found = defaultdict(set)
    for filepath, content in files.items():
        if filepath.suffix != ".md":
            continue
        if "glossary" in str(filepath).lower():
            continue
        for m in GLOSS_REF.finditer(content):
            found[m[1]].add(str(filepath))

    problems = {k:v for k, v in found.items() if len(v) > 1}
    for k, v in problems.items():
        if len(v) > 1:
            print(f"glossary key {k} redefined: {', '.join(sorted(v))}")
    return len(problems) == 0


def lint_glossary_references(opt, files):
    """Check glossary references."""
    available = find_key_defs(files, "glossary")
    if available is None:
        print("No glossary found (or multiple matches)")
        return False
    return check_references(files, "glossary", GLOSS_REF, available)


def lint_link_definitions(opt, files):
    """Check that Markdown files define the links they use."""
    ok = True
    for filepath, content in files.items():
        if filepath.suffix != ".md":
            continue
        link_refs = {m[1] for m in MD_LINK_REF.findall(content)}
        link_defs = {m[0] for m in MD_LINK_DEF.findall(content)}
        ok = ok and report_diff(f"{filepath} links", link_refs, link_defs)
    return ok


def lint_markdown_links(opt, files):
    """Check consistency of Markdown links."""
    found = defaultdict(lambda: defaultdict(set))
    for filepath, content in files.items():
        if filepath.suffix != ".md":
            continue
        for link in MD_LINK_DEF.finditer(content):
            label, url = link.group(1), link.group(2)
            found[label][url].add(filepath)

    ok = True
    for label, data in found.items():
        if len(data) > 1:
            print(f"Inconsistent link: {label} => {data}")
            ok = False
    return ok


def parse_args(parser):
    """Parse command-line arguments."""
    parser.add_argument("--config", type=str, default="pyproject.toml", help="optional configuration file")
    parser.add_argument("--out", type=str, default="docs", help="output directory")
    parser.add_argument("--root", type=str, default=".", help="root directory")
    return parser


def report_diff(msg, refs, defs):
    """Report differences if any."""
    ok = True
    for (kind, vals) in (("missing", refs - defs), ("unused", defs - refs)):
        if vals:
            print(f"{msg} {kind}: {', '.join(vals)}")
            ok = False
    return ok


def resolve_path(source, dest):
    """Account for '..' in paths."""
    while dest[:3] == "../":
        source = source.parent
        dest = dest[3:]
    result = Path(source, dest)
    return result


if __name__ == "__main__":
    opt = parse_args(argparse.ArgumentParser()).parse_args()
    lint(opt)

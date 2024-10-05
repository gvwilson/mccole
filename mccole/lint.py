"""Check site consistency."""

import argparse
from collections import defaultdict
from pathlib import Path
import re

from .util import GLOSS_REF, MD_LINK_DEF, SUFFIXES, find_files, find_key_defs, get_inclusion


BIB_REF = re.compile(r"\[.+?\]\(b:(.+?)\)", re.MULTILINE)
FIGURE_CAPTION = re.compile(r'<figcaption>(.+?)</figcaption>', re.MULTILINE)
FIGURE_DEF = re.compile(r'<figure\s+id="(.+?)"\s*>', re.MULTILINE)
FIGURE_REF = re.compile(r"\[[^\]]+?\]\(f:(.+?)\)", re.MULTILINE)
MD_CODEBLOCK_FILE = re.compile(r'^```\s*\{\s*file="(.+?)"\s*\}\s*$(.+?)```\s*$', re.DOTALL + re.MULTILINE)
MD_FILE_LINK = re.compile(r"\[(.+?)\]\((.+?)\)", re.MULTILINE)
MD_LINK_REF = re.compile(r"\[(.+?)\]\[(.+?)\]", re.MULTILINE)
TABLE_DEF = re.compile(r'<table\s+id="(.+?)"\s*>', re.MULTILINE)
TABLE_REF = re.compile(r"\[[^\]]+?\]\(t:(.+?)\)", re.MULTILINE)


def lint(opt):
    """Main driver."""
    files = find_files(opt, {opt.out})
    check_file_references(files)

    files = {path: data for path, data in files.items() if path.suffix == ".md"}
    extras = {
        "bibliography": find_key_defs(files, "bibliography"),
        "glossary": find_key_defs(files, "glossary"),
    }

    linters = [
        lint_bibliography_references,
        lint_codeblock_inclusions,
        lint_figure_numbers,
        lint_figure_references,
        lint_glossary_redefinitions,
        lint_glossary_references,
        lint_link_definitions,
        lint_markdown_links,
        lint_table_references,
    ]
    sections = {path: data["content"] for path, data in files.items()}
    if all(list(f(opt, sections, extras) for f in linters)):
        print("All self-checks passed.")


def check_file_references(files):
    """Check inter-file references."""
    ok = True
    for path, data in files.items():
        content = data["content"]
        if path.suffix != ".md":
            continue
        for link in MD_FILE_LINK.finditer(content):
            if _is_special_link(link.group(2)):
                continue
            target = _resolve_path(path.parent, link.group(2))
            if _is_missing(target, files):
                print(f"Missing file: {path} => {target}")
                ok = False
    return ok


def lint_bibliography_references(opt, sections, extras):
    """Check bibliography references."""
    available = set(extras["bibliography"].keys())
    if available is None:
        print("No bibliography found (or multiple matches)")
        return False
    return _check_references(sections, "bibliography", BIB_REF, available)


def lint_codeblock_inclusions(opt, sections, extras):
    """Check file inclusions."""
    ok = True
    for path, content in sections.items():
        for block in MD_CODEBLOCK_FILE.finditer(content):
            inc_spec, expected = block.group(1), block.group(2).strip()
            _, _, inc_text = get_inclusion(path, inc_spec)
            if inc_text != expected:
                print(f"Content mismatch: {path} / {inc_spec}")
                ok = False
    return ok


def lint_figure_numbers(opt, sections, extras):
    """Check figure numbering."""
    ok = True
    for path, content in sections.items():
        current = 1
        for caption in FIGURE_CAPTION.finditer(content):
            text = caption.group(1)
            if ("Figure" not in text) or (":" not in text):
                print(f"Bad caption: {path} / '{text}'")
                ok = False
                continue
            fields = text.split(":")
            if len(fields) != 2:
                print(f"Bad caption: {path} / '{text}'")
                ok = False
                continue
            fields = fields[0].split(" ")
            if len(fields) != 2:
                print(f"Bad caption: {path} / '{text}'")
                ok = False
                continue
            try:
                number = int(fields[1])
                if number != current:
                    print(f"Caption number out of sequence: {path} / '{text}'")
                    ok = False
                else:
                    current += 1
            except ValueError:
                print(f"Bad caption number: {path} / '{text}'")
                ok = False
    return ok


def lint_figure_references(opt, sections, extras):
    """Check figure references."""
    return _check_object_refs(sections, "figure", FIGURE_DEF, FIGURE_REF)


def lint_glossary_redefinitions(opt, sections, extras):
    """Check glossary redefinitions."""
    found = defaultdict(set)
    for path, content in sections.items():
        if "glossary" in str(path).lower():
            continue
        for m in GLOSS_REF.finditer(content):
            found[m[1]].add(str(path))

    problems = {k:v for k, v in found.items() if len(v) > 1}
    for k, v in problems.items():
        if len(v) > 1:
            print(f"glossary key {k} redefined: {', '.join(sorted(v))}")
    return len(problems) == 0


def lint_glossary_references(opt, sections, extras):
    """Check glossary references."""
    available = set(extras["glossary"].keys())
    if available is None:
        print("No glossary found (or multiple matches)")
        return False
    return _check_references(sections, "glossary", GLOSS_REF, available)


def lint_link_definitions(opt, sections, extras):
    """Check that Markdown files define the links they use."""
    ok = True
    for path, content in sections.items():
        link_refs = {m[1] for m in MD_LINK_REF.findall(content)}
        link_defs = {m[0] for m in MD_LINK_DEF.findall(content)}
        ok = ok and _report_diff(f"{path} links", link_refs, link_defs)
    return ok


def lint_markdown_links(opt, sections, extras):
    """Check consistency of Markdown links."""
    found = defaultdict(lambda: defaultdict(set))
    for path, content in sections.items():
        for link in MD_LINK_DEF.finditer(content):
            label, url = link.group(1), link.group(2)
            found[label][url].add(path)

    ok = True
    for label, data in found.items():
        if len(data) > 1:
            info = {str(k):", ".join(sorted(str(p) for p in v)) for k, v in data.items()}
            msg = ", ".join(f"{k} in {v}" for k, v in info.items())
            print(f"Inconsistent link {label}: {msg}")
            ok = False
    return ok


def lint_table_references(opt, sections, extras):
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
    for path, content in sections.items():
        defined = set(pattern_def.findall(content))
        referenced = set(pattern_def.findall(content))
        ok = _report_diff(f"{path} {kind}", referenced, defined) and ok
    return ok


def _check_references(sections, term, regexp, available):
    """Check all Markdown files for cross-references."""
    ok = True
    seen = set()
    for path, content in sections.items():
        found = {k.group(1) for k in regexp.finditer(content)}
        seen |= found
        missing = found - available
        if missing:
            print(f"Missing {term} keys in {path}: {', '.join(sorted(missing))}")
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

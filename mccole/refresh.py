"""Refresh file inclusions in place."""

import argparse
from pathlib import Path
import re


COMMENT = {
    "js": "//",
    "py": "#",
    "sql": "--",
}

INC_PAT = re.compile(
    r'^```\s*\{.*?data-file="(.+?)".*?\}.+?^```\s*?$', re.DOTALL + re.MULTILINE
)

INCLUDE_BLOCK = """\
```{{data-file="{path}"}}
{content}\
```\
"""

INCLUDE_BLOCK_KEEP = """\
```{{data-file="{path}:{keep}"}}
{content}\
```\
"""


def main(opt):
    """Refresh inclusions in source file."""
    for filename in opt.files:
        src_path = Path(filename)
        content = src_path.read_text()
        content = INC_PAT.sub(lambda m: _do_inclusion(src_path, m), content)
        src_path.write_text(content)


def construct_parser(parser):
    """Parse command-line arguments."""
    parser.add_argument("--files", nargs="+", help="files to refresh")


def _do_inclusion(outer, match_obj):
    """Refresh content of a single inclusion."""
    spec = match_obj.group(1)
    inner, keep, content = _get_spec(outer, spec)
    if keep is None:
        return INCLUDE_BLOCK.format(path=inner, content=content)
    else:
        content = _extract_section(outer, inner, keep, content)
        return INCLUDE_BLOCK_KEEP.format(path=inner, content=content, keep=keep)


def _extract_section(outer, inner, keep, content):
    """Keep a section of a file."""
    suffix = Path(inner).suffix.lstrip(".")
    assert suffix in COMMENT, f"{outer}: unknown inclusion suffix in {inner}"
    before = f"{COMMENT[suffix]} [{keep}]"
    after = f"{COMMENT[suffix]} [/{keep}]"
    assert (before in content) and (after in content), (
        f"{outer} :: {inner}: missing start/end for {COMMENT[suffix]} and {keep}"
    )
    content = content.split(before)[1].split(after)[0]
    if content[0] == "\n":
        content = content[1:]
    return content


def _get_spec(outer, inner):
    """Load external included file."""
    if ":" in inner:
        inner, keep = inner.split(":")
    else:
        keep = None
    path = outer.parent / inner
    assert path.is_file(), (
        f"Bad inclusion in {outer}: {path} does not exist or is not file"
    )
    return inner, keep, path.read_text()

"""Refresh file inclusions in place."""

import argparse
from pathlib import Path
import re


COMMENT = {
    "js": "//",
    "py": "#",
    "sql": "--",
}

INC_PAT = re.compile(r'^```\s*\{.*?data-file="(.+?)".*?\}.+?^```\s*?$', re.DOTALL + re.MULTILINE)

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

def refresh(opt):
    """Refresh inclusions in source file."""
    for filename in opt.files:
        src_path = Path(filename)
        content = src_path.read_text()
        content = INC_PAT.sub(lambda m: refresh_inclusion(src_path, m), content)
        src_path.write_text(content)


def refresh_inclusion(outer, match_obj):
    """Refresh content of a single inclusion."""
    spec = match_obj.group(1)
    inner, keep, content = inclusion_get(outer, spec)
    if keep is None:
        return INCLUDE_BLOCK.format(path=inner, content=content)
    else:
        content = inclusion_keep(outer, inner, keep, content)
        return INCLUDE_BLOCK_KEEP.format(path=inner, content=content, keep=keep)


def inclusion_get(outer, inner):
    """Load external included file."""
    if ":" in inner:
        inner, keep = inner.split(":")
    else:
        keep = None
    path = outer.parent / inner
    assert path.is_file(), \
        f"Bad inclusion in {outer}: {path} does not exist or is not file"
    return inner, keep, path.read_text()


def inclusion_keep(outer, inner, keep, content):
    """Keep a section of a file."""
    suffix = Path(inner).suffix.lstrip(".")
    assert suffix in COMMENT, \
        f"%inc in {outer}: unknown inclusion suffix in {inner}"
    before = f"{COMMENT[suffix]} [{keep}]"
    after = f"{COMMENT[suffix]} [/{keep}]"
    assert (before in content) and (after in content), \
        f"{outer} :: {inner}: missing start/end for {COMMENT[suffix]} and {keep}"
    content = content.split(before)[1].split(after)[0]
    if content[0] == "\n":
        content = content[1:]
    return content


def parse_args(parser):
    """Parse command-line arguments."""
    parser.add_argument("--files", nargs="+", help="files to refresh")


if __name__ == "__main__":
    opt = parse_args(argparse.ArgumentParser()).parse_args()
    refresh(opt)

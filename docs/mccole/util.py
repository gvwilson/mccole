"""Utilities."""

from pathlib import Path
import re


KEY_DEF = re.compile(r'^<span\s+id="(.+?)">.+?</span>\s*$', re.MULTILINE)
MD_LINK_DEF = re.compile(r"^\[(.+?)\]:\s+(.+?)\s*$", re.MULTILINE)
SUFFIXES_BIN = {".ico", ".jpg", ".png"}
SUFFIXES_SRC = {".css", ".html", ".js", ".md", ".py", ".sh", ".txt"}
SUFFIXES_TXT = SUFFIXES_SRC | {".csv", ".json", ".svg"}
SUFFIXES = SUFFIXES_BIN | SUFFIXES_TXT


def find_files(opt, root_skips=[]):
    """Collect all interesting files."""
    return {
        filepath: read_file(filepath)
        for filepath in Path(opt.root).glob("**/*.*")
        if _is_interesting_file(filepath, root_skips)
    }


def find_key_defs(files, term):
    """Find key definitions in definition list file."""
    candidates = [k for k in files if term in str(k).lower()]
    if len(candidates) != 1:
        return None
    file_key = candidates[0]
    return set(KEY_DEF.findall(files[file_key]))


def find_symlinks(opt, root_skips=[]):
    """Collect all interesting files."""
    return [
        filepath
        for filepath in Path(opt.root).glob("**/*")
        if _is_interesting_symlink(filepath, root_skips)
    ]


def read_file(filepath):
    """Read file as bytes or text."""
    if filepath.suffix in SUFFIXES_TXT:
        return filepath.read_text()
    else:
        return filepath.read_bytes()


def write_file(filepath, content):
    """Write file as bytes or text."""
    if filepath.suffix in SUFFIXES_TXT:
        return filepath.write_text(content)
    else:
        return filepath.write_bytes(content)


def _is_interesting_file(filepath, root_skips):
    """Is this file worth checking?"""
    if not filepath.is_file():
        return False
    if str(filepath).startswith("."):
        return False
    if filepath.suffix not in SUFFIXES:
        return False
    if str(filepath.parent.name).startswith("."):
        return False
    if any(str(filepath).startswith(s) for s in root_skips):
        return False
    return True


def _is_interesting_symlink(filepath, root_skips):
    """Is this symlink worth checking?"""
    if not filepath.is_symlink():
        return False
    if str(filepath).startswith("."):
        return False
    if any(str(filepath).startswith(s) for s in root_skips):
        return False
    return True

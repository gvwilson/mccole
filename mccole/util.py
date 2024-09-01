"""Utilities."""

from collections import defaultdict
from pathlib import Path
import re
import tomli


DEFAULT_CONFIG = {
    "duplicates": set(),
    "skips": set(),
}
FIGURE_DEF = re.compile(r'<figure\s+id="(.+?)"\s*>\s+<img\s+src="(.+?)"\s+alt="(.+?)"\s*>\s+<figcaption>(.+?)</figcaption>\s+</figure>', re.MULTILINE)
KEY_DEF = re.compile(r'^<span\s+id="(.+?)">.+?</span>\s*$', re.MULTILINE)
MD_LINK_DEF = re.compile(r"^\[(.+?)\]:\s+(.+?)\s*$", re.MULTILINE)
SUFFIXES_BIN = {".ico", ".jpg", ".png"}
SUFFIXES_SRC = {".css", ".html", ".js", ".md", ".py", ".sh", ".sql", ".txt"}
SUFFIXES_TXT = SUFFIXES_SRC | {".csv", ".json", ".svg"}
SUFFIXES = SUFFIXES_BIN | SUFFIXES_TXT
TABLE_DEF = re.compile(r'<table\s+id="(.+?)"\s*>.+?<caption>(.+?)</caption>\s*</table>', re.MULTILINE + re.DOTALL)


def find_figure_defs(files):
    """Collect all figure definitions."""
    found = defaultdict(list)
    for filepath, content in files.items():
        if filepath.suffix == ".md":
            for figure in FIGURE_DEF.finditer(content):
                found[figure[1]].append({
                    "img": figure[2],
                    "alt": figure[3],
                    "caption": figure[4],
                })
    return found


def find_files(opt, skips=[]):
    """Collect all interesting files."""
    return {
        filepath: read_file(filepath)
        for filepath in Path(opt.root).glob("**/*.*")
        if _is_interesting_file(filepath, skips)
    }


def find_key_defs(files, term):
    """Find key definitions in definition list file."""
    candidates = [k for k in files if term in str(k).lower()]
    if len(candidates) != 1:
        return None
    file_key = candidates[0]
    return set(KEY_DEF.findall(files[file_key]))


def find_symlinks(opt, skips=[]):
    """Collect all interesting files."""
    return [
        filepath
        for filepath in Path(opt.root).glob("**/*")
        if _is_interesting_symlink(filepath, skips)
    ]


def find_table_defs(files):
    """Collect all table definitions."""
    found = defaultdict(list)
    for filepath, content in files.items():
        if filepath.suffix == ".md":
            for table in TABLE_DEF.finditer(content):
                found[table[1]].append({"caption": table[2],})
    return found


def load_config(config_path):
    """Load configuration file or construct default."""
    if config_path is None:
        return DEFAULT_CONFIG
    config = tomli.loads(Path(config_path).read_text())
    if ("tool" not in config) or ("mccole" not in config["tool"]):
        print(f"configuration file {config_path} does not have 'tool.mccole' section")
        return DEFAULT_CONFIG
    config = config["tool"]["mccole"]
    if "duplicates" in config:
        config["duplicates"] = set(frozenset(v) for v in config["duplicates"])
    if "skips" in config:
        config["skips"] = set(config["skips"])
    return config


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


def _is_interesting_file(filepath, skips):
    """Is this file worth checking?"""
    if not filepath.is_file():
        return False
    if str(filepath).startswith("."):
        return False
    if filepath.suffix not in SUFFIXES:
        return False
    if str(filepath.parent.name).startswith("."):
        return False
    if any(str(filepath).startswith(s) for s in skips):
        return False
    return True


def _is_interesting_symlink(filepath, skips):
    """Is this symlink worth checking?"""
    if not filepath.is_symlink():
        return False
    if str(filepath).startswith("."):
        return False
    if any(str(filepath).startswith(s) for s in skips):
        return False
    return True

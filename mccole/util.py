"""Utilities."""

from collections import defaultdict
from git import Repo
from github import Github
from pathlib import Path
import re
import tomli


DEFAULT_CONFIG = {
    "duplicates": set(),
    "skips": set(),
}
FIGURE_DEF = re.compile(r'<figure\s+id="(.+?)"\s*>\s+<img\s+src="(.+?)"\s+alt="(.+?)"\s*>\s+<figcaption>(.+?)</figcaption>\s+</figure>', re.MULTILINE)
GLOSS_REF = re.compile(r"\[[^\]]+?\]\(g:(.+?)\)", re.MULTILINE)
KEY_DEF = re.compile(r'^<span\s+id="(.+?)">(.+?)</span>\s*$', re.MULTILINE)
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


def find_files(opt, skips=None):
    """Collect all interesting files."""
    return {
        filepath: read_file(filepath)
        for filepath in Path(opt.root).glob("**/*.*")
        if _is_interesting_file(filepath, skips)
    }


def find_key_defs(files, term, subkey=None):
    """Find key definitions in definition list file."""
    candidates = [k for k in files if term in str(k).lower()]
    if len(candidates) != 1:
        return None
    file_key = candidates[0]
    content = files[file_key] if subkey is None else files[file_key][subkey]
    return {m[0]:m[1] for m in KEY_DEF.findall(content)}


def find_table_defs(files):
    """Collect all table definitions."""
    found = defaultdict(list)
    for filepath, content in files.items():
        if filepath.suffix == ".md":
            for table in TABLE_DEF.finditer(content):
                found[table[1]].append({"caption": table[2],})
    return found


def get_inclusion(source_path, inc_spec):
    """Load inclusion, returning path, suffix, and text."""
    if ":" in inc_spec:
        assert inc_spec.count(":") == 1, f"Bad inclusion spec '{inc_spec}' in {source_path}"
        inc_file, mark = inc_spec.split(":")
        assert inc_file and mark, f"Bad inclusion spec '{inc_spec}' in {source_path}"
    else:
        inc_file, mark = inc_spec, None
    inc_path = Path(source_path.parent, inc_file)
    inc_text = inc_path.read_text().strip()
    if mark is not None:
        start, end = f"[{mark}]", f"[/{mark}]"
        assert (inc_text.count(start) == 1) and (inc_text.count(end) == 1), \
            f"Bad start '{start}' and/or end '{end}' in {inc_spec} in {source_path}"
        inc_text = inc_text.split(start)[1].split(end)[0]
        inc_text = inc_text[:inc_text.rfind("\n")].strip()
    suffix = inc_path.suffix.lstrip(".")
    return inc_path, suffix, inc_text


def get_repo(root_dir):
    """Get GitHub repository object for this project."""
    repo = Repo(root_dir)
    url = list(repo.remotes["origin"].urls)[0]
    if "@github.com" in url:
        user_proj = url.split(":")[1].replace(".git", "")
    else:
        user_proj = url.replace("https://github.com/", "").lstrip("/")
    return Github().get_repo(user_proj)


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
    filepath.parent.mkdir(parents=True, exist_ok=True)
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
    if skips and any(str(filepath).startswith(s) for s in skips):
        return False
    return True

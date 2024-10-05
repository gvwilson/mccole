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
GLOSS_REF = re.compile(r"\[[^\]]+?\]\(g:(.+?)\)", re.MULTILINE)
KEY_DEF = re.compile(r'^<span\s+id="(.+?)">(.+?)</span>\s*$', re.MULTILINE)
MD_LINK_DEF = re.compile(r"^\[(.+?)\]:\s+(.+?)\s*$", re.MULTILINE)
SUFFIXES_BIN = {".ico", ".jpg", ".png"}
SUFFIXES_SRC = {".css", ".html", ".js", ".md", ".py", ".sh", ".sql", ".txt"}
SUFFIXES_TXT = SUFFIXES_SRC | {".csv", ".json", ".svg"}
SUFFIXES = SUFFIXES_BIN | SUFFIXES_TXT
TABLE_DEF = re.compile(r'<table\s+id="(.+?)"\s*>.+?<caption>(.+?)</caption>\s*</table>', re.DOTALL + re.MULTILINE)


def find_files(opt, skips=None):
    """Collect all interesting files."""
    return {
        path: {"content": read_file(path)}
        for path in Path(opt.root).glob("**/*.*")
        if _is_interesting_file(path, skips)
    }


def find_key_defs(files, term):
    """Find key definitions in definition list file."""
    candidates = [k for k in files if term in str(k).lower()]
    if len(candidates) != 1:
        return None
    file_key = candidates[0]
    return {m[0]:m[1] for m in KEY_DEF.findall(files[file_key]["content"])}


def find_table_defs(files):
    """Collect all table definitions."""
    found = defaultdict(list)
    for path, content in files.items():
        if path.suffix == ".md":
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


def read_file(path):
    """Read file as bytes or text."""
    if path.suffix in SUFFIXES_TXT:
        return path.read_text()
    else:
        return path.read_bytes()


def write_file(path, content):
    """Write file as bytes or text."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix in SUFFIXES_TXT:
        return path.write_text(content)
    else:
        return path.write_bytes(content)


def _is_interesting_file(path, skips):
    """Is this file worth checking?"""
    if not path.is_file():
        return False
    if str(path).startswith("."):
        return False
    if path.suffix not in SUFFIXES:
        return False
    if str(path.parent.name).startswith("."):
        return False
    if skips and any(str(path).startswith(s) for s in skips):
        return False
    return True

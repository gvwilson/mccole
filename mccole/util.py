"""Utilities."""

from collections import defaultdict
from git import Repo
from github import Github
from pathlib import Path
import re
import tomli

ALSO_HTML_SUFFIX = {".css", ".js", ".py", ".sql"}
DEFAULT_CONFIG = {
    "renames": {},
    "skips": set(),
}
GLOSS_REF = re.compile(r"\[[^\]]+?\]\(g:(.+?)\)", re.MULTILINE)
KEY_DEF = re.compile(r'^<span\s+id="(.+?)">(.+?)</span>\s*$', re.MULTILINE)
LINK_DEF = re.compile(r'<a\s+id="(.+?)"\s+href="(.+?)"\s*>(.+?)</a>\s*$', re.MULTILINE)
SUFFIXES_BIN = {".ico", ".jpg", ".png", ".webp"}
SUFFIXES_TXT = {".css", "csv", ".html", ".js", "json", ".md", ".py", ".sh", ".sql", ".svg", ".txt"}
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

    config["skips"] = set(config["skips"]) if "skips" in config else set()

    if "renames" not in config:
        config["renames"] = {}

    overlap = set(config["renames"].keys()) & config["skips"]
    if overlap:
        print(f"overlap between skips and renames in configuration: {', '.join(sorted(overlap))}")

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

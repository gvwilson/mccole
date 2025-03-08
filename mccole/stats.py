"""Report site stats."""

import argparse
from collections import defaultdict
from prettytable import PrettyTable
import re

from .util import find_files, find_key_defs, find_table_defs, get_repo


FIGURE_DEF = re.compile(r"\[%\s*figure\b(.+?)%\]", re.DOTALL + re.MULTILINE)
FIGURE_ALT = re.compile(r'alt="(.+?)"', re.MULTILINE)
FIGURE_CAPTION = re.compile(r'caption="(.+?)"', re.MULTILINE)
FIGURE_ID = re.compile(r'id="(.+?)"', re.MULTILINE)
FIGURE_SRC = re.compile(r'src="(.+?)"', re.MULTILINE)
TABLE_FMT = {
    "stat": "l",
    "value": "r",
}


def stats(opt):
    """Main driver."""
    table = PrettyTable(field_names=TABLE_FMT.keys())
    for k, v in TABLE_FMT.items():
        table.align[k] = v

    files = find_files(opt, {opt.out})
    table.add_row(("bibliography entries", len(find_key_defs(files, "bibliography"))))
    table.add_row(("glossary entries", len(find_key_defs(files, "glossary"))))

    sections = {path: data["content"] for path, data in files.items()}
    table.add_row(("figures", len(find_figure_defs(sections))))
    table.add_row(("tables", len(find_table_defs(sections))))
    table.add_row(("issues", get_num_issues(opt.root)))
    table.add_row(("pull requests", get_num_pull_requests(opt.root)))

    print(table)


def find_figure_defs(files):
    """Collect all figure definitions."""
    found = defaultdict(list)
    for path, content in files.items():
        if path.suffix == ".md":
            for figure in FIGURE_DEF.finditer(content):
                text = figure.group(1)
                found[FIGURE_ID.search(text).group(1)].append({
                    "src": FIGURE_SRC.search(text).group(1),
                    "alt": FIGURE_ALT.search(text).group(1),
                    "caption": FIGURE_CAPTION.search(text).group(1),
                })
    return found


def get_num_issues(root):
    """Get issue count from repository."""
    return get_repo(root).open_issues_count


def get_num_pull_requests(root):
    """Get pull request count from repository."""
    return get_repo(root).get_pulls().totalCount


def parse_args(parser):
    """Parse command-line arguments."""
    parser.add_argument("--out", type=str, default="docs", help="output directory")
    parser.add_argument("--root", type=str, default=".", help="root directory")
    return parser


if __name__ == "__main__":
    opt = parse_args(argparse.ArgumentParser()).parse_args()
    stats(opt)

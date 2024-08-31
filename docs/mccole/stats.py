"""Report site stats."""

import argparse
from prettytable import PrettyTable
import re

from .util import FIGURE_DEF, MD_LINK_DEF, find_figure_defs, find_files, find_key_defs


TABLE_FMT = {
    "stat": "l",
    "value": "r",
}


def stats(opt):
    """Main driver."""
    table = PrettyTable(field_names=TABLE_FMT.keys())
    for k, v in TABLE_FMT.items():
        table.align[k] = v

    files = find_files(opt, set(["bin", opt.out]))
    table.add_row(("bibliography entries", len(find_key_defs(files, "bibliography"))))
    table.add_row(("glossary entries", len(find_key_defs(files, "glossary"))))
    table.add_row(("figures", len(find_figure_defs(files))))
    table.add_row(("link definitions", len(find_markdown_link_defs(files))))

    print(table)


def find_markdown_link_defs(files):
    """Collect Markdown link key definnitions."""
    found = set()
    for filepath, content in files.items():
        if filepath.suffix == ".md":
            for link in MD_LINK_DEF.finditer(content):
                found.add(link[0])
    return found


def parse_args(parser):
    """Parse command-line arguments."""
    parser.add_argument("--out", type=str, default="docs", help="output directory")
    parser.add_argument("--root", type=str, default=".", help="root directory")
    return parser


if __name__ == "__main__":
    opt = parse_args(argparse.ArgumentParser()).parse_args()
    stats(opt)

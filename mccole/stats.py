"""Report site stats."""

import argparse
from prettytable import PrettyTable

from .util import MD_LINK_DEF, find_figure_defs, find_files, find_key_defs, find_table_defs, get_repo


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
    table.add_row(("figures", len(find_figure_defs(files))))
    table.add_row(("link definitions", len(find_markdown_link_defs(files))))
    table.add_row(("tables", len(find_table_defs(files))))
    table.add_row(("issues", get_num_issues(opt.root)))
    table.add_row(("pull requests", get_num_pull_requests(opt.root)))

    print(table)


def find_markdown_link_defs(files):
    """Collect Markdown link key definnitions."""
    found = set()
    for filepath, content in files.items():
        if filepath.suffix == ".md":
            for link in MD_LINK_DEF.finditer(content):
                found.add(link[0])
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

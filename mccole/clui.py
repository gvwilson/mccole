"""Interface for command-line script."""

import argparse
import importlib.metadata
import sys

from .build import build, construct_parser as build_parser
from .init import init, construct_parser as init_parser
from .lint import lint, construct_parser as lint_parser


def main():
    """Main driver."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action="store_true", help="show version")

    subparsers = parser.add_subparsers(dest="cmd")
    build_parser(subparsers.add_parser("build", help="build site"))
    init_parser(subparsers.add_parser("init", help="(re-)initialize site"))
    lint_parser(subparsers.add_parser("lint", help="check site"))

    opt = parser.parse_args()
    if opt.version:
        print(importlib.metadata.version("mccole"))
    elif opt.cmd == "build":
        build(opt)
    elif opt.cmd == "init":
        init(opt)
    elif opt.cmd == "lint":
        lint(opt)
    else:
        print(f"unknown command {opt.cmd}", file=sys.stderr)
        sys.exit(1)

"""Interface for command-line script."""

import argparse
import cProfile
import importlib.metadata
import pstats
import sys

from .build import build, parse_args as build_parser
from .install import install, parse_args as install_parser
from .lint import lint, parse_args as lint_parser
from .refresh import refresh, parse_args as refresh_parser
from .stats import stats, parse_args as stats_parser


def main():
    """Main driver."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action="store_true", help="show version")

    subparsers = parser.add_subparsers(dest="cmd")
    build_parser(subparsers.add_parser("build", help="build site"))
    install_parser(subparsers.add_parser("install", help="install files"))
    lint_parser(subparsers.add_parser("lint", help="check site"))
    build_parser(subparsers.add_parser("profile", help="profile building site"))
    refresh_parser(subparsers.add_parser("refresh", help="check site"))
    stats_parser(subparsers.add_parser("stats", help="show stats"))

    opt = parser.parse_args()
    if opt.version:
        print(importlib.metadata.version("mccole"))
    elif opt.cmd == "build":
        build(opt)
    elif opt.cmd == "install":
        install(opt)
    elif opt.cmd == "lint":
        lint(opt)
    elif opt.cmd == "profile":
        with cProfile.Profile() as profiler:
            build(opt)
            result = pstats.Stats(profiler)
            result.sort_stats("tottime")
            result.print_stats(16)
    elif opt.cmd == "refresh":
        refresh(opt)
    elif opt.cmd == "stats":
        stats(opt)
    else:
        print(f"unknown command {opt.cmd}", file=sys.stderr)
        sys.exit(1)

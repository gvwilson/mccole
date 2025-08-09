"""Interface for command-line script."""

import argparse
import importlib.metadata
import sys

from .build import main as build, construct_parser as build_parser
from .init import main as init, construct_parser as init_parser
from .lint import main as lint, construct_parser as lint_parser
from .refresh import main as refresh, construct_parser as refresh_parser


COMMANDS = {
    "build": (build, build_parser, "build site"),
    "init": (init, init_parser, "(re-)initialize site"),
    "lint": (lint, lint_parser, "check site"),
    "refresh": (refresh, refresh_parser, "refresh inclusions"),
}


def main():
    """Main driver."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action="store_true", help="show version")

    subparsers = parser.add_subparsers(dest="cmd")
    for cmd, (_, p, text) in COMMANDS.items():
        p(subparsers.add_parser(cmd, help=text))

    opt = parser.parse_args()
    if opt.version:
        print(importlib.metadata.version("mccole"))
    if opt.cmd in COMMANDS:
        COMMANDS[opt.cmd][0](opt)
    else:
        print(f"unknown command {opt.cmd}", file=sys.stderr)
        sys.exit(1)

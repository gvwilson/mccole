"""Command-line user interface."""

import argparse
import importlib.metadata
from pathlib import Path
import sys

from .build import build
from .check import check
from .create import create


def main():
    """Main driver."""
    commands = {
        "build": (build, _make_build_parser, "build site"),
        "check": (check, _make_check_parser, "check site"),
        "create": (create, _make_create_parser, "create site"),
    }
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", type=int, default=0, help="logging level")
    parser.add_argument("--version", action="store_true", help="show version")

    subparsers = parser.add_subparsers(dest="command")
    for cmd, (_, p, text) in commands.items():
        p(subparsers.add_parser(cmd, help=text))

    args = parser.parse_args()
    if args.version:
        print(importlib.metadata.version("mccole"))
    elif args.command in commands:
        commands[args.command][0](args)
    else:
        print(f"unknown command {args.command}", file=sys.stderr)
        sys.exit(1)


def _make_build_parser(parser):
    """Parse command-line arguments for building site."""
    parser.add_argument(
        "--config", default=Path("pyproject.toml"), help="configuration file"
    )
    parser.add_argument(
        "--dst", type=Path, default=Path("docs"), help="destination directory"
    )
    parser.add_argument(
        "--root", type=Path, default=Path("README.md"), help="root page file"
    )
    parser.add_argument("--src", type=Path, default=Path("."), help="source directory")


def _make_check_parser(parser):
    """Parse command-line arguments for checking site."""
    parser.add_argument(
        "--config", default=Path("pyproject.toml"), help="configuration file"
    )
    parser.add_argument(
        "--dst", type=Path, default=Path("docs"), help="destination directory"
    )
    parser.add_argument("--html", action="store_true", help="validate HTML")
    parser.add_argument("--src", type=Path, default=Path("."), help="source directory")


def _make_create_parser(parser):
    """Parse command-line arguments for creating or refreshing files."""
    parser.add_argument("--dst", type=Path, default=".", help="destination directory")
    parser.add_argument("--force", action="store_true", help="force overwrite")
    parser.add_argument(
        "--only", type=Path, nargs="+", help="only install specific files"
    )

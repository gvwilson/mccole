"""Command-line user interface."""

import argparse
import importlib.metadata
from pathlib import Path
import sys

from .bib import bib
from .build import build
from .check import check
from .create import create
from .describe import describe
from .single_page import build_single_page


def main():
    """Main driver."""
    commands = {
        "bib": (bib, _make_bib_parser, "validate bibliography"),
        "build": (build, _make_build_parser, "build site"),
        "check": (check, _make_check_parser, "check site"),
        "create": (create, _make_create_parser, "create site"),
        "describe": (describe, _make_describe_parser, "describe lesson contents"),
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
        result = commands[args.command][0](args)
        if args.command == "build" and getattr(args, "single_page", None):
            config, env = result
            build_single_page(config, env, args.single_page)
    else:
        print(f"unknown command {args.command}", file=sys.stderr)
        sys.exit(1)


def _make_bib_parser(parser):
    """Parse command-line arguments for validating bibliography."""
    parser.add_argument(
        "--config", default=Path("pyproject.toml"), help="configuration file"
    )
    parser.add_argument("--src", type=Path, default=Path("."), help="source directory")


def _make_build_parser(parser):
    """Parse command-line arguments for building site."""
    parser.add_argument(
        "--config", default=Path("pyproject.toml"), help="configuration file"
    )
    parser.add_argument(
        "--dst", type=Path, default=Path("docs"), help="destination directory"
    )
    parser.add_argument("--extra", type=Path, default=None, help="extra HTML to include in page <head>")
    parser.add_argument("--single-page", type=Path, default=None, help="output path for single-page version")
    parser.add_argument("--forma", action="store_true", help="enable formative assessments")
    parser.add_argument("--math", action="store_true", help="enable KaTeX math rendering")
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
    parser.add_argument(
        "--root", type=Path, default=Path("README.md"), help="root page file"
    )
    parser.add_argument("--src", type=Path, default=Path("."), help="source directory")


def _make_create_parser(parser):
    """Parse command-line arguments for creating or refreshing files."""
    parser.add_argument("--dst", type=Path, default=".", help="destination directory")
    parser.add_argument("--force", action="store_true", help="force overwrite")
    parser.add_argument(
        "--only", type=Path, nargs="+", help="only install specific files"
    )


def _make_describe_parser(parser):
    """Parse command-line arguments for describing lesson contents."""
    parser.add_argument("--inc", action="store_true", help="show table of file inclusions")
    parser.add_argument(
        "--root", type=Path, default=Path("README.md"), help="root page file"
    )
    parser.add_argument("--src", type=Path, default=Path("."), help="source directory")

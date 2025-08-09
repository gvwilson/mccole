"""Install files needed for building sites."""

import argparse
import importlib.resources
from pathlib import Path
import sys


def main(opt):
    """Main driver."""
    src = importlib.resources.files(__name__.split(".")[0]) / "data"
    available = {
        filename: opt.dst / filename.relative_to(src)
        for filename in src.glob("**/*")
        if filename.is_file()
    }
    if opt.only:
        available = {
            filename: path
            for filename, path in available.items()
            if filename.relative_to(src) in opt.only
        }

    exists = {str(dst) for dst in available.values() if dst.exists()}
    if exists and (not opt.force):
        print(
            f"not overwriting {', '.join(sorted(exists))} (use --force)",
            file=sys.stderr,
        )
        sys.exit(1)

    opt.dst.mkdir(parents=True, exist_ok=True)
    for src, dst in available.items():
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())


def construct_parser(parser):
    """Parse command-line arguments."""
    parser.add_argument("--dst", type=Path, default=".", help="destination directory")
    parser.add_argument("--force", action="store_true", help="force overwrite")
    parser.add_argument(
        "--only", type=Path, nargs="+", help="only install specific files"
    )

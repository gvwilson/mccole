"""McCole package."""

import argparse
import os
import pkg_resources as pkg
import shutil
import sys


__version__ = "0.14.0"
__author__ = "Greg Wilson"


ARCHIVE = "mccole.zip"
DATADIR = "data"


def main():
    """Main driver."""
    options = parse_args()
    reader = pkg.resource_stream(__name__, os.path.join(DATADIR, ARCHIVE))
    content = reader.read()
    with open(os.path.join(options.root, ARCHIVE), "wb") as writer:
        writer.write(content)
    shutil.unpack_archive(ARCHIVE)
    os.remove(ARCHIVE)


def parse_args():
    """Get command-line options."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Where to install")
    return parser.parse_args()

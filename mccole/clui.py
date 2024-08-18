'''Interface for command-line script.'''

import argparse
import importlib.metadata
import importlib.resources
from pathlib import Path
import sys

from .lint import lint, parse_args as lint_parser
from .render import render, parse_args as render_parser


INSTALL_FILES = (
    'templates/page.html',
    'templates/slides.html',
    'static/page.css',
    'static/slides.css',
    'static/slides.js',
)


def main():
    '''Main driver.'''
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='store_true', help='show version')
    subparsers = parser.add_subparsers(dest='cmd')
    install_parser(subparsers.add_parser('install', help='install files'))
    lint_parser(subparsers.add_parser('lint', help='check site'))
    render_parser(subparsers.add_parser('render', help='build site'))
    opt = parser.parse_args()
    if opt.version:
        print(importlib.metadata.version('mccole'))
    elif opt.cmd == 'install':
        install(opt)
    elif opt.cmd == 'lint':
        lint(opt)
    elif opt.cmd == 'render':
        render(opt)
    else:
        print(f'unknown command {opt.cmd}', file=sys.stderr)
        sys.exit(1)


def install(opt):
    '''Install package files.'''
    outdir = Path(opt.root)
    outdir.mkdir(parents=True, exist_ok=True)
    root = importlib.resources.files(__name__.split('.')[0])
    mapping = {
        root.joinpath(filename): outdir.joinpath(Path(filename))
        for filename in INSTALL_FILES
    }

    exists = {str(dst) for dst in mapping.values() if dst.exists()}
    if exists and (not opt.force):
        print(f'not overwriting {", ".join(sorted(exists))} (use --force)', file=sys.stderr)
        sys.exit(1)

    for src, dst in mapping.items():
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
    

def install_parser(parser):
    '''Parse command-line arguments.'''
    parser.add_argument('--force', action='store_true', help='overwrite')
    parser.add_argument('--root', type=str, default='.', help='root directory')
    return parser

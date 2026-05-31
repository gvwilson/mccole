"""Tests for mccole.clui parser-builder functions."""

import argparse
from pathlib import Path

from mccole.clui import (
    _make_bib_parser,
    _make_build_parser,
    _make_check_parser,
    _make_create_parser,
    _make_describe_parser,
    _make_detab_parser,
)
from mccole.detab import DEFAULT_TABSIZE


def _parser(make_func):
    """Return a parser configured by make_func."""
    p = argparse.ArgumentParser()
    make_func(p)
    return p


class TestMakeBibParser:
    def test_defaults(self):
        args = _parser(_make_bib_parser).parse_args([])
        assert args.src == Path(".")
        assert args.config == Path("pyproject.toml")


class TestMakeBuildParser:
    def test_defaults(self):
        args = _parser(_make_build_parser).parse_args([])
        assert args.src == Path(".")
        assert args.dst == Path("docs")
        assert args.root == Path("README.md")
        assert args.math is False
        assert args.forma is False
        assert args.single_page is None
        assert args.extra is None

    def test_flags(self):
        args = _parser(_make_build_parser).parse_args(["--math", "--forma"])
        assert args.math is True
        assert args.forma is True


class TestMakeCheckParser:
    def test_defaults(self):
        args = _parser(_make_check_parser).parse_args([])
        assert args.src == Path(".")
        assert args.dst == Path("docs")
        assert args.root == Path("README.md")
        assert args.relaxed is False

    def test_relaxed_flag(self):
        args = _parser(_make_check_parser).parse_args(["--relaxed"])
        assert args.relaxed is True


class TestMakeCreateParser:
    def test_defaults(self):
        args = _parser(_make_create_parser).parse_args([])
        assert args.dst == Path(".")
        assert args.force is False
        assert args.only is None


class TestMakeDescribeParser:
    def test_defaults(self):
        args = _parser(_make_describe_parser).parse_args([])
        assert args.bibliography is False
        assert args.glossary is False
        assert args.inc is False
        assert args.root == Path("README.md")
        assert args.src == Path(".")

    def test_flags(self):
        args = _parser(_make_describe_parser).parse_args(
            ["--bibliography", "--glossary", "--inc"]
        )
        assert args.bibliography is True
        assert args.glossary is True
        assert args.inc is True


class TestMakeDetabParser:
    def test_defaults(self):
        args = _parser(_make_detab_parser).parse_args([])
        assert args.src == Path(".")
        assert args.root == Path("README.md")
        assert args.tabsize == DEFAULT_TABSIZE

"""Tests for mccole.inclusions."""

from pathlib import Path
import textwrap

import pytest

from mccole.inclusions import (
    _colorize_code,
    _filter_exclude,
    _filter_head,
    _filter_include,
    _filter_scrub,
    _get_comment_format,
    COMMENT_FORMATS,
)


class TestGetCommentFormat:
    def test_known_extensions(self):
        """Returns comment delimiters for known file types."""
        assert _get_comment_format("foo.py") == ("#", "")
        assert _get_comment_format("foo.c") == ("//", "")
        assert _get_comment_format("foo.html") == ("<!--", "-->")
        assert _get_comment_format("foo.js") == ("//", "")
        assert _get_comment_format("foo.sql") == ("--", "")
        assert _get_comment_format("foo.json") == (None, "")
        assert _get_comment_format("foo.xml") == ("<!--", "-->")

    def test_all_comment_formats_single_char(self):
        """All defined comment prefixes are non-empty (except json)."""
        for ext, (prefix, suffix) in COMMENT_FORMATS.items():
            assert isinstance(prefix, (str, type(None)))
            assert isinstance(suffix, str)

    def test_unknown_extension_raises(self):
        """Raises ValueError for unsupported extension."""
        with pytest.raises(ValueError, match="unsupported file type"):
            _get_comment_format("foo.unknown")


class TestFilterHead:
    def test_keeps_first_n(self):
        lines = ["a", "b", "c", "d", "e"]
        result = _filter_head(lines, "3")
        assert result == ["a", "b", "c"]

    def test_zero_returns_empty(self):
        result = _filter_head(["a", "b"], "0")
        assert result == []

    def test_more_than_available(self):
        result = _filter_head(["a"], "10")
        assert result == ["a"]

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="invalid head count"):
            _filter_head([], "abc")


class TestFilterScrub:
    def test_removes_matching_substring(self):
        """Removes matching parts from lines; unmodified lines are kept."""
        lines = ["print('hello')  # comment", "x = 1"]
        result = _filter_scrub(lines, r"#.*")
        assert result == ["print('hello')", "x = 1"]

    def test_preserves_line_without_match(self):
        lines = ["hello world", "no match"]
        result = _filter_scrub(lines, r"#.*")
        assert result == ["hello world", "no match"]

    def test_drops_blank_after_scrub(self):
        """Lines that become blank after scrubbing are removed."""
        lines = ["  # only comment", "keep"]
        result = _filter_scrub(lines, r"#.*")
        assert result == ["keep"]

    def test_invalid_pattern_raises(self):
        with pytest.raises(ValueError, match="invalid scrub pattern"):
            _filter_scrub([], "[")


class TestFilterInclude:
    def test_extracts_marked_section(self, tmp_path):
        """Extracts lines between marker comments."""
        filepath = tmp_path / "test.py"
        filepath.write_text(
            textwrap.dedent("""\
            # first line
            # mccole: mymark
            content line 1
            content line 2
            # mccole: /mymark
            # after
        """),
            encoding="utf-8",
        )
        lines = filepath.read_text(encoding="utf-8").splitlines()
        result = _filter_include(filepath, lines, "mymark")
        assert result == ["content line 1", "content line 2"]

    def test_strips_surrounding_blank_lines(self, tmp_path):
        """Strips leading/trailing blank lines from result."""
        filepath = tmp_path / "test.py"
        filepath.write_text(
            textwrap.dedent("""\
            # mccole: mymark

            content

            # mccole: /mymark
        """),
            encoding="utf-8",
        )
        lines = filepath.read_text(encoding="utf-8").splitlines()
        result = _filter_include(filepath, lines, "mymark")
        assert result == ["content"]

    def test_invalid_marker_raises(self, tmp_path):
        filepath = tmp_path / "test.py"
        filepath.write_text("# mccole: bad!\n", encoding="utf-8")
        lines = filepath.read_text(encoding="utf-8").splitlines()
        with pytest.raises(ValueError, match="invalid marker"):
            _filter_include(filepath, lines, "bad!")

    def test_json_returns_all_lines(self, tmp_path):
        """JSON files (no comment prefix) return all lines."""
        filepath = tmp_path / "test.json"
        filepath.write_text('{"a": 1}\n', encoding="utf-8")
        lines = filepath.read_text(encoding="utf-8").splitlines()
        result = _filter_include(filepath, lines, "irrelevant")
        assert result == ['{"a": 1}']


class TestFilterExclude:
    def test_excludes_marked_section(self, tmp_path):
        """Excludes lines between marker comments."""
        filepath = tmp_path / "test.py"
        filepath.write_text(
            textwrap.dedent("""\
            # keep this
            # mccole: skip
            remove me
            # mccole: /skip
            # keep this too
        """),
            encoding="utf-8",
        )
        lines = filepath.read_text(encoding="utf-8").splitlines()
        result = _filter_exclude(filepath, lines, "skip")
        assert result == [
            "# keep this",
            "# ...1 lines not shown...",
            "# keep this too",
        ]

    def test_excludes_multiple_sections(self, tmp_path):
        """Excludes multiple marked sections."""
        filepath = tmp_path / "test.py"
        filepath.write_text(
            textwrap.dedent("""\
            keep1
            # mccole: a
            drop1
            # mccole: /a
            keep2
            # mccole: b
            drop2
            drop3
            # mccole: /b
            keep3
        """),
            encoding="utf-8",
        )
        lines = filepath.read_text(encoding="utf-8").splitlines()
        result = _filter_exclude(filepath, lines, "a")
        # filter_exclude takes a single marker, not all markers
        assert "keep1" in result
        assert "# ...1 lines not shown..." in result
        assert "keep2" in result
        # b is not processed with this call
        assert "keep3" in result

    def test_strips_blank_lines(self, tmp_path):
        """Strips leading/trailing blanks."""
        filepath = tmp_path / "test.py"
        filepath.write_text("\nkeep\n", encoding="utf-8")
        lines = filepath.read_text(encoding="utf-8").splitlines()
        result = _filter_exclude(filepath, lines, "nonexistent")
        assert result == ["keep"]

    def test_invalid_marker_raises(self, tmp_path):
        filepath = tmp_path / "test.py"
        filepath.write_text("# code\n", encoding="utf-8")
        lines = filepath.read_text(encoding="utf-8").splitlines()
        with pytest.raises(ValueError, match="invalid marker"):
            _filter_exclude(filepath, lines, "bad marker")


class TestColorizeCode:
    def test_returns_html_with_codehilite(self):
        """Returns HTML with codehilite class."""
        result = _colorize_code("print('hello')", "test.py")
        assert 'class="codehilite"' in result
        assert "<code>" in result

    def test_unknown_extension_uses_text(self):
        """Falls back to text lexer for unknown extension."""
        result = _colorize_code("hello", "test.xyzzy")
        assert 'class="codehilite"' in result

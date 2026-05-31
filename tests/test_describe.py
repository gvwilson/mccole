"""Tests for mccole.describe."""

from pathlib import Path
import textwrap

from mccole.describe import (
    _all_entries,
    _apply_filters,
    _describe_bibliography,
    _describe_glossary,
    _describe_inclusions,
    _find_inclusions,
)


class TestApplyFilters:
    def test_no_filters(self, tmp_path):
        """Returns all lines when no filters are applied."""
        filepath = tmp_path / "test.py"
        filepath.write_text("a\nb\nc\n", encoding="utf-8")
        lines, mods = _apply_filters(filepath, {})
        assert lines == ["a", "b", "c"]
        assert mods == ""

    def test_mark_filter(self, tmp_path):
        """Applies mark filter."""
        filepath = tmp_path / "test.py"
        filepath.write_text(
            textwrap.dedent("""\
            # mccole: mymark
            content
            # mccole: /mymark
        """),
            encoding="utf-8",
        )
        lines, mods = _apply_filters(filepath, {"mark": "mymark"})
        assert lines == ["content"]
        assert "mark=mymark" in mods

    def test_omit_filter(self, tmp_path):
        """Applies omit filter."""
        filepath = tmp_path / "test.py"
        filepath.write_text(
            textwrap.dedent("""\
            keep
            # mccole: skip
            drop
            # mccole: /skip
        """),
            encoding="utf-8",
        )
        lines, mods = _apply_filters(filepath, {"omit": "skip"})
        assert "keep" in lines
        assert "drop" not in lines
        assert "omit=skip" in mods

    def test_head_filter(self, tmp_path):
        """Applies head filter."""
        filepath = tmp_path / "test.py"
        filepath.write_text("a\nb\nc\n", encoding="utf-8")
        lines, mods = _apply_filters(filepath, {"head": "2"})
        assert lines == ["a", "b"]
        assert "head=2" in mods

    def test_scrub_filter(self, tmp_path):
        """Applies scrub filter."""
        filepath = tmp_path / "test.py"
        filepath.write_text("hello # comment\nworld\n", encoding="utf-8")
        lines, mods = _apply_filters(filepath, {"scrub": r"#.*"})
        assert lines == ["hello", "world"]
        assert "scrub=#.*" in mods

    def test_multiple_filters(self, tmp_path):
        """Combines multiple filters in mods string."""
        filepath = tmp_path / "test.py"
        filepath.write_text("# mccole: m\ncontent\n# mccole: /m\n", encoding="utf-8")
        lines, mods = _apply_filters(filepath, {"mark": "m", "head": "10"})
        assert lines == ["content"]
        assert "mark=m, head=10" in mods


class TestFindInclusions:
    def test_finds_inc_shortcodes(self, tmp_path):
        """Finds [%inc%] shortcode references."""
        src = tmp_path / "src"
        src.mkdir()
        md_path = src / "index.md"
        md_path.write_text("[%inc test.py %]\n", encoding="utf-8")
        inc_file = src / "test.py"
        inc_file.write_text("line1\nline2\n", encoding="utf-8")

        results = list(_find_inclusions(md_path, md_path.read_text(encoding="utf-8")))
        assert len(results) == 1
        filename, mods, line_count = results[0]
        assert filename == "test.py"
        assert line_count == 2

    def test_pat_expansion(self, tmp_path):
        """Handles [%inc pat=... fill=... %] pattern expansion."""
        src = tmp_path / "src"
        src.mkdir()
        md_path = src / "index.md"
        md_path.write_text('[%inc pat=file_*.py fill="a" %]\n', encoding="utf-8")
        (src / "file_a.py").write_text("hello\n", encoding="utf-8")

        results = list(_find_inclusions(md_path, md_path.read_text(encoding="utf-8")))
        assert len(results) == 1
        assert results[0][0] == "file_a.py"

    def test_missing_files_skipped(self, tmp_path):
        """Missing files are skipped."""
        src = tmp_path / "src"
        src.mkdir()
        md_path = src / "index.md"
        md_path.write_text("[%inc no_such.py %]\n", encoding="utf-8")

        results = list(_find_inclusions(md_path, md_path.read_text(encoding="utf-8")))
        assert len(results) == 0


class TestAllEntries:
    def test_returns_order_entries(self, src_dir):
        """_all_entries returns one entry per lesson and appendix."""
        class Opts:
            src = src_dir
            root = Path("README.md")

        entries = _all_entries(Opts())
        filepaths = [e["filepath"] for e in entries]
        assert src_dir / "intro" / "index.md" in filepaths
        assert src_dir / "refs" / "index.md" in filepaths

    def test_includes_slides(self, tmp_path):
        """Slide entries are appended after lesson/appendix entries."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "README.md").write_text(
            textwrap.dedent("""\
            # Book
            <div id="lessons" markdown="1">
            -   [Intro](@/intro/)
            </div>
            <div id="appendices" markdown="1">
            </div>
            <div id="slides">
            <a href="@/intro/slides.html">Intro Slides</a>
            </div>
            """),
            encoding="utf-8",
        )
        (src / "intro").mkdir()
        (src / "intro" / "index.md").write_text("# Intro\n", encoding="utf-8")
        (src / "_extras").mkdir()
        (src / "_extras" / "links.md").write_text("", encoding="utf-8")

        class Opts:
            root = Path("README.md")

        Opts.src = src
        entries = _all_entries(Opts())
        filepaths = [e["filepath"] for e in entries]
        assert src / "intro" / "slides.md" in filepaths


class TestDescribeBibliography:
    def test_no_refs_silent(self, src_dir, capsys):
        """Prints nothing when no [%b%] shortcodes found."""
        class Opts:
            src = src_dir
            root = Path("README.md")

        _describe_bibliography(Opts())
        assert capsys.readouterr().out == ""

    def test_with_refs_prints_table(self, src_with_glossary_bib, capsys):
        """Prints a table when [%b%] shortcodes are found."""
        class Opts:
            src = src_with_glossary_bib
            root = Path("README.md")

        _describe_bibliography(Opts())
        out = capsys.readouterr().out
        assert "Key2020" in out
        assert "Key" in out and "Files" in out


class TestDescribeGlossary:
    def test_no_refs_silent(self, src_dir, capsys):
        """Prints nothing when no [%g%] shortcodes found."""
        class Opts:
            src = src_dir
            root = Path("README.md")

        _describe_glossary(Opts())
        assert capsys.readouterr().out == ""

    def test_with_refs_prints_table(self, src_with_glossary_bib, capsys):
        """Prints a table when [%g%] shortcodes are found."""
        class Opts:
            src = src_with_glossary_bib
            root = Path("README.md")

        _describe_glossary(Opts())
        out = capsys.readouterr().out
        assert "term1" in out
        assert "Key" in out and "Files" in out


class TestDescribeInclusions:
    def test_no_inclusions_silent(self, src_dir, capsys):
        """Prints nothing when no [%inc%] shortcodes found."""
        class Opts:
            src = src_dir
            root = Path("README.md")

        _describe_inclusions(Opts())
        assert capsys.readouterr().out == ""

    def test_with_inclusions_prints_table(self, src_dir, capsys):
        """Prints a table when [%inc%] shortcodes with existing files are found."""
        helper = src_dir / "intro" / "helper.py"
        helper.write_text("line1\nline2\n", encoding="utf-8")
        (src_dir / "intro" / "index.md").write_text(
            "# Intro\n\n[%inc helper.py %]\n", encoding="utf-8"
        )

        class Opts:
            src = src_dir
            root = Path("README.md")

        _describe_inclusions(Opts())
        out = capsys.readouterr().out
        assert "helper.py" in out
        assert "2" in out

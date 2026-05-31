"""Tests for mccole.shortcodes."""

import io
from pathlib import Path
import textwrap

import mccole.shortcodes as shortcodes
from mccole import util

from mccole.shortcodes import (
    process_shortcodes,
    _page_slug,
    _crossref_link,
    _missing_shortcode_arg,
)


class TestPageSlug:
    def test_readme_is_home(self):
        assert _page_slug(Path("/test/README.md")) == "home"

    def test_lesson_is_parent_name(self):
        assert _page_slug(Path("/test/intro/index.md")) == "intro"


class TestCrossrefLink:
    def test_builds_anchor(self):
        result = _crossref_link("gl-ref", "@/glossary/#x", "display")
        assert result == '<a class="gl-ref" href="@/glossary/#x">display</a>'

    def test_empty_text(self):
        result = _crossref_link("xref", "@/slug/")
        assert result == '<a class="xref" href="@/slug/"></a>'


class TestMissingShortcodeArg:
    def test_warns_and_returns_default(self, capsys):
        buf = io.StringIO()
        old = shortcodes.util.sys.stderr
        shortcodes.util.sys.stderr = buf
        try:
            result = _missing_shortcode_arg("tag", "name", Path("test.md"), "fallback")
        finally:
            shortcodes.util.sys.stderr = old
        assert result == "fallback"
        assert "missing name" in buf.getvalue()


class TestProcessShortcodesBasic:
    def test_unknown_shortcode_preserved(self, basic_config):
        """Unknown tags are left as-is with a warning."""
        buf = io.StringIO()
        old = shortcodes.util.sys.stderr
        shortcodes.util.sys.stderr = buf
        try:
            result = process_shortcodes(
                "[%unknown arg%]", basic_config, Path("test.md"), []
            )
        finally:
            shortcodes.util.sys.stderr = old
        assert "[%unknown arg%]" in result
        assert "unknown shortcode" in buf.getvalue()

    def test_closing_tag_stripped(self, basic_config):
        """Closing tags are silently removed."""
        result = process_shortcodes("[%/g%]", basic_config, Path("test.md"), [])
        assert result == ""

    def test_shlex_fallback(self, basic_config):
        """When shlex fails, falls back to split."""
        result = process_shortcodes(
            '[%g key "display" unmatched%]', basic_config, Path("test.md"), []
        )
        assert 'class="gl-ref"' in result


class TestShortcodeB:
    def test_bibliography_link(self, basic_config):
        result = process_shortcodes("[%b Key2020 %]", basic_config, Path("test.md"), [])
        assert 'class="bib-ref"' in result
        assert "@/bibliography/#Key2020" in result
        assert "Key2020" in result


class TestShortcodeG:
    def test_glossary_link_with_display(self, basic_config):
        result = process_shortcodes(
            '[%g term "the term" %]', basic_config, Path("test.md"), []
        )
        assert 'class="gl-ref"' in result
        assert "@/glossary/#term" in result
        assert "the term" in result

    def test_glossary_link_without_display(self, basic_config):
        result = process_shortcodes("[%g term %]", basic_config, Path("test.md"), [])
        assert ">term</a>" in result

    def test_missing_key(self, basic_config):
        buf = io.StringIO()
        old = shortcodes.util.sys.stderr
        shortcodes.util.sys.stderr = buf
        try:
            result = process_shortcodes("[%g %]", basic_config, Path("test.md"), [])
        finally:
            shortcodes.util.sys.stderr = old
        assert result == ""
        assert "missing key" in buf.getvalue()


class TestShortcodeF:
    def test_figure_crossref(self, basic_config):
        result = process_shortcodes("[%f fig1 %]", basic_config, Path("test.md"), [])
        assert 'class="fig-ref"' in result
        assert "#f:fig1" in result


class TestShortcodeT:
    def test_table_crossref(self, basic_config):
        result = process_shortcodes("[%t tbl1 %]", basic_config, Path("test.md"), [])
        assert 'class="tbl-ref"' in result
        assert "#t:tbl1" in result


class TestShortcodeX:
    def test_crossref_to_known_slug(self, basic_config):
        result = process_shortcodes("[%x intro %]", basic_config, Path("test.md"), [])
        assert 'class="xref"' in result
        assert "@/intro/" in result
        assert "Chapter 1" in result

    def test_crossref_to_unknown_slug(self, basic_config):
        buf = io.StringIO()
        old = shortcodes.util.sys.stderr
        shortcodes.util.sys.stderr = buf
        try:
            result = process_shortcodes(
                "[%x no_such %]", basic_config, Path("test.md"), []
            )
        finally:
            shortcodes.util.sys.stderr = old
        assert "@/no_such/" in result


class TestShortcodeI:
    def test_index_entry(self, basic_config):
        ix_entries = []
        result = process_shortcodes(
            '[%i "mykey" "display text" %]',
            basic_config,
            Path("intro/index.md"),
            ix_entries,
        )
        assert 'class="ix-ref"' in result
        assert "display text" in result
        assert len(ix_entries) == 1
        assert ix_entries[0]["key"] == "mykey"
        assert ix_entries[0]["text"] == "display text"
        assert ix_entries[0]["slug"] == "intro"
        assert ix_entries[0]["uid"].startswith("ix-intro-")

    def test_index_without_display(self, basic_config):
        ix_entries = []
        result = process_shortcodes(
            '[%i "keyonly" %]', basic_config, Path("test.md"), ix_entries
        )
        assert ix_entries[0]["text"] == "keyonly"


class TestShortcodeLinecount:
    def test_counts_non_blank_lines(self, tmp_path, basic_config):
        src = tmp_path / "site"
        src.mkdir()
        src_path = src / "index.md"
        src_path.write_text("hello\n", encoding="utf-8")
        code_file = src / "test.py"
        code_file.write_text("line1\n\nline2\n\n\nline3\n", encoding="utf-8")
        result = process_shortcodes(
            "[%linecount test.py %]", basic_config, src_path, []
        )
        assert result == "3"

    def test_missing_file_returns_zero(self, basic_config):
        buf = io.StringIO()
        old = shortcodes.util.sys.stderr
        shortcodes.util.sys.stderr = buf
        try:
            result = process_shortcodes(
                "[%linecount no_such.py %]", basic_config, Path("test.md"), []
            )
        finally:
            shortcodes.util.sys.stderr = old
        assert result == "0"


class TestShortcodeInc:
    def test_basic_include_div(self, basic_config):
        result = process_shortcodes(
            "[%inc test.py %]", basic_config, Path("lesson/index.md"), []
        )
        assert '<div data-inc="test.py"></div>' in result

    def test_with_filters(self, basic_config):
        result = process_shortcodes(
            "[%inc test.py mark=m omit=o head=5 scrub=s %]",
            basic_config,
            Path("lesson/index.md"),
            [],
        )
        assert 'data-inc="test.py"' in result
        assert 'data-mark="m"' in result
        assert 'data-omit="o"' in result
        # head and omit are mutually exclusive
        assert 'data-head="5"' not in result
        assert 'data-scrub="s"' in result

    def test_head_only(self, basic_config):
        result = process_shortcodes(
            "[%inc test.py head=3 %]",
            basic_config,
            Path("lesson/index.md"),
            [],
        )
        assert 'data-head="3"' in result

    def test_pattern_expansion(self, tmp_path, basic_config):
        """Pattern expansion generates divs for matching files that exist."""
        lesson = tmp_path / "lesson"
        lesson.mkdir(parents=True)
        src_path = lesson / "index.md"
        src_path.write_text("", encoding="utf-8")
        (lesson / "file_a.py").write_text("hello\n", encoding="utf-8")
        (lesson / "file_b.py").write_text("world\n", encoding="utf-8")
        result = process_shortcodes(
            '[%inc pat=file_*.py fill="a b" %]',
            basic_config,
            src_path,
            [],
        )
        assert '<div data-inc="file_a.py"></div>' in result
        assert '<div data-inc="file_b.py"></div>' in result
        assert 'class="continuation"' in result


class TestShortcodeFigure:
    def test_basic_figure(self, basic_config):
        result = process_shortcodes(
            '[% figure slug="fig1" img="pic.png" alt="Alt" caption="Cap" %]',
            basic_config,
            Path("test.md"),
            [],
        )
        assert '<figure id="f:fig1">' in result
        assert '<img src="pic.png"' in result
        assert "Alt" in result
        assert "Cap" in result


class TestShortcodeTable:
    def test_table_shortcode(self, tmp_path, basic_config):
        src_path = tmp_path / "src" / "index.md"
        src_path.parent.mkdir(parents=True, exist_ok=True)
        src_path.write_text("", encoding="utf-8")
        tbl_file = src_path.parent / "data.md"
        tbl_file.write_text("| a | b |\n|---|---|\n", encoding="utf-8")
        result = process_shortcodes(
            '[% table slug="t1" tbl="data.md" caption="C" %]',
            basic_config,
            src_path,
            [],
        )
        assert '<div id="t:t1"' in result
        assert 'data-caption="C"' in result
        assert "| a | b |" in result


class TestShortcodeFixme:
    def test_fixme(self, basic_config):
        result = process_shortcodes(
            '[%fixme "do this" %]', basic_config, Path("test.md"), []
        )
        assert 'class="fixme"' in result
        assert "do this" in result

    def test_default_text(self, basic_config):
        result = process_shortcodes("[%fixme %]", basic_config, Path("test.md"), [])
        assert "FIXME" in result


class TestShortcodeIssue:
    def test_with_repo(self, basic_config):
        result = process_shortcodes("[%issue 42 %]", basic_config, Path("test.md"), [])
        assert "issues/42" in result
        assert "issue 42" in result

    def test_without_repo(self, basic_config):
        basic_config["repo"] = ""
        result = process_shortcodes("[%issue 42 %]", basic_config, Path("test.md"), [])
        assert "issue 42" in result
        assert 'class="issue"' in result


class TestShortcodeThanks:
    def test_thanks_with_yaml(self, tmp_path, basic_config):
        extras = tmp_path / "extras"
        extras.mkdir()
        basic_config["extras"] = extras
        thanks = extras / "thanks.yml"
        thanks.write_text(
            textwrap.dedent("""\
            - personal: Alice
              family: Smith
            - personal: Bob
              family: Jones
              order: fp
        """),
            encoding="utf-8",
        )
        result = process_shortcodes("[% thanks %]", basic_config, Path("test.md"), [])
        assert "Alice Smith" in result
        assert "Jones Bob" in result
        assert "and" in result

    def test_single_contributor(self, tmp_path, basic_config):
        extras = tmp_path / "extras"
        extras.mkdir()
        basic_config["extras"] = extras
        (extras / "thanks.yml").write_text(
            "- personal: Alice\n  family: Smith\n", encoding="utf-8"
        )
        result = process_shortcodes("[% thanks %]", basic_config, Path("test.md"), [])
        assert result == "Alice Smith"

    def test_missing_file_returns_default(self, basic_config):
        buf = io.StringIO()
        old = shortcodes.util.sys.stderr
        shortcodes.util.sys.stderr = buf
        try:
            result = process_shortcodes(
                "[% thanks %]", basic_config, Path("test.md"), []
            )
        finally:
            shortcodes.util.sys.stderr = old
        assert "the contributors" in result


class TestShortcodesWithGlossaryBib:
    def test_glossary_and_bib_links(self, src_with_glossary_bib):
        """[%g%] and [%b%] produce correct links against a real source tree."""
        src = src_with_glossary_bib
        config = {
            "src": src,
            "dst": src.parent / "docs",
            "home_page": Path("README.md"),
            "links": util.load_links(src),
            "order": util.load_order(src, Path("README.md")),
            "templates": src.parent / "_templates",
            "repo": "",
            "extras": src / "_extras",
            "lang": "en",
            "math": False,
            "forma": False,
            "extra_html": "",
        }
        content = (src / "lesson1" / "index.md").read_text(encoding="utf-8")
        result = process_shortcodes(content, config, src / "lesson1" / "index.md", [])
        assert 'class="gl-ref"' in result
        assert "@/glossary/#term1" in result
        assert 'class="bib-ref"' in result
        assert "@/bibliography/#Key2020" in result

"""Tests for mccole.check."""

import io
from pathlib import Path

from bs4 import BeautifulSoup

import mccole.check as check_mod
from mccole.check import (
    _check_bibliography_alphabetical,
    _check_bibliography_bare_isbns,
    _check_bibliography_key_mismatch,
    _check_cross_references,
    _check_empty_inclusions,
    _check_figure_structure,
    _check_glossary_alphabetical,
    _check_glossary_redefinitions,
    _check_single_h1,
    _check_table_structure,
    _check_tabs_in_markdown,
    _check_unknown_links,
    _check_unused_crossref_definitions,
)


def _soup(html):
    return BeautifulSoup(html, "html.parser")


class _Opts:
    def __init__(self, dst=None, src=None, root=None):
        self.dst = dst if dst is not None else Path("/fake")
        self.src = src
        self.root = root


def _bib_page(*keys):
    """Build a bibliography HTML page with given keys."""
    items = "".join(
        f'<dt><span id="{k}">{k}</span></dt><dd>Entry for {k}.</dd>' for k in keys
    )
    return _soup(f"<dl>{items}</dl>")


def _gloss_page(*pairs):
    """Build a glossary HTML page with (id, display_text) pairs."""
    items = "".join(
        f'<dt><span id="{tid}">{text}</span></dt><dd>Def.</dd>'
        for tid, text in pairs
    )
    return _soup(f"<dl>{items}</dl>")


def _capture(func, *args, **kwargs):
    """Call func capturing stderr; return (result, stderr_text)."""
    buf = io.StringIO()
    old = check_mod.sys.stderr
    check_mod.sys.stderr = buf
    try:
        result = func(*args, **kwargs)
    finally:
        check_mod.sys.stderr = old
    return result, buf.getvalue()


class TestCheckCrossReferences:
    def test_valid_reference_ok(self, tmp_path):
        opts = _Opts(dst=tmp_path)
        pages = {
            tmp_path / "bibliography" / "index.html": _bib_page("Key2020"),
            tmp_path / "page" / "index.html": _soup(
                '<a href="/bibliography/#Key2020">Key2020</a>'
            ),
        }
        _, err = _capture(_check_cross_references, opts, pages, "bibliography")
        assert "unknown" not in err

    def test_unknown_key_reported(self, tmp_path):
        opts = _Opts(dst=tmp_path)
        pages = {
            tmp_path / "bibliography" / "index.html": _bib_page("Key2020"),
            tmp_path / "page" / "index.html": _soup(
                '<a href="/bibliography/#Missing">Missing</a>'
            ),
        }
        _, err = _capture(_check_cross_references, opts, pages, "bibliography")
        assert "unknown bibliography key Missing" in err

    def test_missing_definition_page_reported(self, tmp_path):
        opts = _Opts(dst=tmp_path)
        _, err = _capture(_check_cross_references, opts, {}, "bibliography")
        assert "not found" in err


class TestCheckUnusedCrossrefDefinitions:
    def test_all_keys_used_ok(self, tmp_path):
        opts = _Opts(dst=tmp_path)
        pages = {
            tmp_path / "bibliography" / "index.html": _bib_page("Key2020"),
            tmp_path / "page" / "index.html": _soup(
                '<a href="/bibliography/#Key2020">Key2020</a>'
            ),
        }
        _, err = _capture(_check_unused_crossref_definitions, opts, pages, "bibliography")
        assert "unused" not in err

    def test_unused_key_reported(self, tmp_path):
        opts = _Opts(dst=tmp_path)
        pages = {
            tmp_path / "bibliography" / "index.html": _bib_page("Key2020"),
        }
        _, err = _capture(_check_unused_crossref_definitions, opts, pages, "bibliography")
        assert "unused bibliography key Key2020" in err


class TestCheckGlossaryRedefinitions:
    def test_single_page_reference_ok(self, tmp_path):
        pages = {
            tmp_path / "a" / "index.html": _soup(
                '<a href="/glossary/#t1" class="gl-ref">t1</a>'
            ),
        }
        _, err = _capture(_check_glossary_redefinitions, pages)
        assert "defined in" not in err

    def test_term_defined_links_excluded(self, tmp_path):
        """Links with class term-defined are not counted."""
        pages = {
            tmp_path / "a" / "index.html": _soup(
                '<a href="/glossary/#t1" class="term-defined">t1</a>'
            ),
            tmp_path / "b" / "index.html": _soup(
                '<a href="/glossary/#t1" class="term-defined">t1</a>'
            ),
        }
        _, err = _capture(_check_glossary_redefinitions, pages)
        assert "defined in" not in err

    def test_multiple_page_references_reported(self, tmp_path):
        pages = {
            tmp_path / "a" / "index.html": _soup(
                '<a href="/glossary/#t1" class="gl-ref">t1</a>'
            ),
            tmp_path / "b" / "index.html": _soup(
                '<a href="/glossary/#t1" class="gl-ref">t1</a>'
            ),
        }
        _, err = _capture(_check_glossary_redefinitions, pages)
        assert "glossary entry 't1' defined in" in err


class TestCheckBibliographyAlphabetical:
    def test_in_order_ok(self, tmp_path):
        opts = _Opts(dst=tmp_path)
        pages = {
            tmp_path / "bibliography" / "index.html": _bib_page("Alpha2000", "Beta2010"),
        }
        _, err = _capture(_check_bibliography_alphabetical, opts, pages)
        assert "out-of-order" not in err

    def test_out_of_order_reported(self, tmp_path):
        opts = _Opts(dst=tmp_path)
        pages = {
            tmp_path / "bibliography" / "index.html": _bib_page("Beta2010", "Alpha2000"),
        }
        _, err = _capture(_check_bibliography_alphabetical, opts, pages)
        assert "out-of-order key Alpha2000" in err


class TestCheckGlossaryAlphabetical:
    def test_in_order_ok(self, tmp_path):
        opts = _Opts(dst=tmp_path)
        pages = {
            tmp_path / "glossary" / "index.html": _gloss_page(
                ("t1", "apple"), ("t2", "banana")
            ),
        }
        _, err = _capture(_check_glossary_alphabetical, opts, pages)
        assert "out-of-order" not in err

    def test_out_of_order_reported(self, tmp_path):
        opts = _Opts(dst=tmp_path)
        pages = {
            tmp_path / "glossary" / "index.html": _gloss_page(
                ("t1", "banana"), ("t2", "apple")
            ),
        }
        _, err = _capture(_check_glossary_alphabetical, opts, pages)
        assert "out-of-order term 'apple'" in err

    def test_missing_glossary_page_reported(self, tmp_path):
        opts = _Opts(dst=tmp_path)
        _, err = _capture(_check_glossary_alphabetical, opts, {})
        assert "not found" in err


class TestCheckBibliographyKeyMismatch:
    def test_matching_id_and_text_ok(self, tmp_path):
        opts = _Opts(dst=tmp_path)
        pages = {tmp_path / "bibliography" / "index.html": _bib_page("Key2020")}
        _, err = _capture(_check_bibliography_key_mismatch, opts, pages)
        assert "mismatch" not in err

    def test_mismatch_reported(self, tmp_path):
        opts = _Opts(dst=tmp_path)
        html = '<dl><dt><span id="Key2020">WrongText</span></dt><dd>Entry.</dd></dl>'
        pages = {tmp_path / "bibliography" / "index.html": _soup(html)}
        _, err = _capture(_check_bibliography_key_mismatch, opts, pages)
        assert "key mismatch" in err

    def test_missing_bib_page_reported(self, tmp_path):
        opts = _Opts(dst=tmp_path)
        _, err = _capture(_check_bibliography_key_mismatch, opts, {})
        assert "not found" in err


class TestCheckBibliographyBareIsbns:
    def test_linked_isbn_ok(self, tmp_path):
        opts = _Opts(dst=tmp_path)
        html = (
            '<dl><dt><span id="K">K</span></dt>'
            '<dd><a href="x">9780306406157</a></dd></dl>'
        )
        pages = {tmp_path / "bibliography" / "index.html": _soup(html)}
        _, err = _capture(_check_bibliography_bare_isbns, opts, pages)
        assert "bare ISBN" not in err

    def test_bare_isbn_reported(self, tmp_path):
        opts = _Opts(dst=tmp_path)
        html = (
            '<dl><dt><span id="K">K</span></dt>'
            '<dd>See 9780306406157 for details.</dd></dl>'
        )
        pages = {tmp_path / "bibliography" / "index.html": _soup(html)}
        _, err = _capture(_check_bibliography_bare_isbns, opts, pages)
        assert "bare ISBN" in err

    def test_missing_bib_page_is_silent(self, tmp_path):
        """No error when bibliography page is absent (function returns early)."""
        opts = _Opts(dst=tmp_path)
        _, err = _capture(_check_bibliography_bare_isbns, opts, {})
        assert err == ""


class TestCheckTabsInMarkdown:
    def test_no_tabs_ok(self, src_dir):
        class Opts:
            src = src_dir
            root = Path("README.md")

        _, err = _capture(_check_tabs_in_markdown, Opts())
        assert "tab character" not in err

    def test_tab_reported(self, src_dir):
        (src_dir / "intro" / "index.md").write_text(
            "# Intro\n\thello\n", encoding="utf-8"
        )

        class Opts:
            src = src_dir
            root = Path("README.md")

        _, err = _capture(_check_tabs_in_markdown, Opts())
        assert "tab character" in err


class TestCheckUnknownLinks:
    def test_brackets_in_code_ok(self):
        opts = _Opts()
        doc = _soup("<pre><code>[link][ref]</code></pre>")
        _, err = _capture(_check_unknown_links, opts, Path("test.html"), doc)
        assert "unresolved" not in err

    def test_brackets_in_paragraph_reported(self):
        opts = _Opts()
        doc = _soup("<p>[link][ref]</p>")
        _, err = _capture(_check_unknown_links, opts, Path("test.html"), doc)
        assert "unresolved Markdown link" in err


class TestCheckSingleH1:
    def test_one_h1_ok(self):
        opts = _Opts()
        doc = _soup("<h1>Title</h1><p>content</p>")
        _, err = _capture(_check_single_h1, opts, Path("test.html"), doc)
        assert err == ""

    def test_no_h1_reported(self):
        opts = _Opts()
        doc = _soup("<p>No heading</p>")
        _, err = _capture(_check_single_h1, opts, Path("test.html"), doc)
        assert "0 H1" in err

    def test_two_h1s_reported(self):
        opts = _Opts()
        doc = _soup("<h1>A</h1><h1>B</h1>")
        _, err = _capture(_check_single_h1, opts, Path("test.html"), doc)
        assert "2 H1" in err


class TestCheckEmptyInclusions:
    def test_nonempty_inclusion_ok(self):
        opts = _Opts()
        doc = _soup('<div data-inc="test.py"><pre>content</pre></div>')
        _, err = _capture(_check_empty_inclusions, opts, Path("test.html"), doc)
        assert "empty" not in err

    def test_empty_inclusion_reported(self):
        opts = _Opts()
        doc = _soup('<div data-inc="test.py"><pre>   </pre></div>')
        _, err = _capture(_check_empty_inclusions, opts, Path("test.html"), doc)
        assert "empty inclusion" in err

    def test_inclusion_without_pre_ok(self):
        """A div[data-inc] without a <pre> is not flagged."""
        opts = _Opts()
        doc = _soup('<div data-inc="test.py"></div>')
        _, err = _capture(_check_empty_inclusions, opts, Path("test.html"), doc)
        assert "empty" not in err

    def test_inc_path_from_span_title(self):
        """inc_path is taken from span.inc-path title when present."""
        opts = _Opts()
        doc = _soup(
            '<div data-inc="x.py">'
            '<span class="inc-path" title="real/path.py"></span>'
            "<pre>   </pre>"
            "</div>"
        )
        _, err = _capture(_check_empty_inclusions, opts, Path("test.html"), doc)
        assert "empty inclusion of real/path.py" in err


class TestCheckFigureStructure:
    def test_valid_figure_ok(self):
        opts = _Opts()
        doc = _soup(
            '<figure id="f:fig1"><figcaption>Figure 1: caption</figcaption></figure>'
        )
        _, err = _capture(_check_figure_structure, opts, Path("test.html"), doc)
        assert err == ""

    def test_missing_id_reported(self):
        opts = _Opts()
        doc = _soup('<figure><figcaption>Figure 1: caption</figcaption></figure>')
        _, err = _capture(_check_figure_structure, opts, Path("test.html"), doc)
        assert "missing 'id'" in err

    def test_missing_caption_reported(self):
        opts = _Opts()
        doc = _soup('<figure id="f:fig1"></figure>')
        _, err = _capture(_check_figure_structure, opts, Path("test.html"), doc)
        assert "missing/extra figure caption(s)" in err

    def test_bad_caption_format_reported(self):
        opts = _Opts()
        doc = _soup('<figure id="f:fig1"><figcaption>Bad caption</figcaption></figure>')
        _, err = _capture(_check_figure_structure, opts, Path("test.html"), doc)
        assert "badly-formatted" in err


class TestCheckTableStructure:
    def test_valid_table_ok(self):
        opts = _Opts()
        doc = _soup(
            '<div data-caption="x" id="t:tab1">'
            "<table><caption>Table 1: desc</caption></table>"
            "</div>"
        )
        _, err = _capture(_check_table_structure, opts, Path("test.html"), doc)
        assert err == ""

    def test_missing_id_reported(self):
        opts = _Opts()
        doc = _soup(
            '<div data-caption="x">'
            "<table><caption>Table 1: desc</caption></table>"
            "</div>"
        )
        _, err = _capture(_check_table_structure, opts, Path("test.html"), doc)
        assert "missing 'id'" in err

    def test_bad_caption_format_reported(self):
        opts = _Opts()
        doc = _soup(
            '<div data-caption="x" id="t:tab1">'
            "<table><caption>Bad caption</caption></table>"
            "</div>"
        )
        _, err = _capture(_check_table_structure, opts, Path("test.html"), doc)
        assert "badly-formatted" in err

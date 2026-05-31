"""Tests for mccole.single_page."""

from bs4 import BeautifulSoup

from mccole.single_page import (
    _apply_compound_figure_numbers,
    _apply_compound_table_numbers,
    _bump_headings,
    _namespace_ids,
    _namespace_intrapage_hrefs,
    _rewrite_at_links,
    _rewrite_image_paths,
    _rewrite_special_links,
)


def _parse(html):
    return BeautifulSoup(html, "html.parser")


class TestBumpHeadings:
    def test_bumps_all_headings(self):
        doc = _parse("<main><h1>A</h1><h2>B</h2><h3>C</h3></main>")
        main = doc.find("main")
        _bump_headings(main)
        assert main.find("h2") is not None
        assert main.find("h2").string == "A"
        assert main.find("h3").string == "B"
        assert main.find("h4").string == "C"

    def test_bumps_h5_to_h6(self):
        doc = _parse("<main><h5>lowest</h5></main>")
        main = doc.find("main")
        _bump_headings(main)
        assert main.find("h6") is not None
        assert main.find("h6").string == "lowest"


class TestNamespaceIds:
    def test_prefixes_ids(self):
        doc = _parse('<div id="abc"><span id="def"></span></div>')
        _namespace_ids(doc, "slug")
        assert doc.find("div")["id"] == "slug--abc"
        assert doc.find("span")["id"] == "slug--def"


class TestNamespaceIntrapageHrefs:
    def test_prefixes_hash_hrefs(self):
        doc = _parse('<a href="#abc">link</a><a href="http://x.com">ext</a>')
        _namespace_intrapage_hrefs(doc, "slug")
        assert doc.select("a")[0]["href"] == "#slug--abc"
        assert doc.select("a")[1]["href"] == "http://x.com"


class TestRewriteSpecialLinks:
    def test_rewrites_g_prefix(self):
        doc = _parse('<a href="g:mykey">text</a>')
        _rewrite_special_links(doc)
        assert doc.find("a")["href"] == "#glossary--mykey"

    def test_rewrites_b_prefix(self):
        doc = _parse('<a href="b:mykey">text</a>')
        _rewrite_special_links(doc)
        assert doc.find("a")["href"] == "#bibliography--mykey"


class TestRewriteAtLinks:
    def test_home_link(self):
        doc = _parse('<a href="@/">Home</a>')
        _rewrite_at_links(doc)
        assert doc.find("a")["href"] == "#home"

    def test_glossary_link(self):
        doc = _parse('<a href="@/glossary/#xyz">def</a>')
        _rewrite_at_links(doc)
        assert doc.find("a")["href"] == "#glossary--xyz"

    def test_bibliography_link(self):
        doc = _parse('<a href="@/bibliography/#abc">ref</a>')
        _rewrite_at_links(doc)
        assert doc.find("a")["href"] == "#bibliography--abc"

    def test_slug_with_anchor(self):
        doc = _parse('<a href="@/intro/#section">link</a>')
        _rewrite_at_links(doc)
        assert doc.find("a")["href"] == "#intro--section"

    def test_slug_only(self):
        doc = _parse('<a href="@/intro/">link</a>')
        _rewrite_at_links(doc)
        assert doc.find("a")["href"] == "#intro"

    def test_img_src(self):
        doc = _parse('<img src="@/_static/pic.png"/>')
        _rewrite_at_links(doc)
        assert doc.find("img")["src"] == "_static/pic.png"


class TestRewriteImagePaths:
    """Tests for _rewrite_image_paths."""

    def test_prefixes_relative_paths(self):
        doc = _parse('<img src="file.png"/><img src="/abs.png"/>')
        _rewrite_image_paths(doc, "intro")
        assert doc.select("img")[0]["src"] == "intro/file.png"
        assert doc.select("img")[1]["src"] == "/abs.png"

    def test_preserves_http_src(self):
        doc = _parse('<img src="http://example.com/pic.png"/>')
        _rewrite_image_paths(doc, "intro")
        assert doc.find("img")["src"] == "http://example.com/pic.png"

    def test_preserves_data_uri(self):
        doc = _parse('<img src="data:image/png;base64,abc"/>')
        _rewrite_image_paths(doc, "intro")
        assert doc.find("img")["src"] == "data:image/png;base64,abc"

    def test_preserves_static_prefix(self):
        doc = _parse('<img src="_static/pic.png"/>')
        _rewrite_image_paths(doc, "intro")
        assert doc.find("img")["src"] == "_static/pic.png"


class TestApplyCompoundFigureNumbers:
    def test_numbers_figures_and_fills_refs(self):
        doc = _parse(
            "<main>"
            '<figure id="f:fig1"><figcaption>desc</figcaption></figure>'
            '<figure id="f:fig2"><figcaption>desc2</figcaption></figure>'
            '<a href="#f:fig1"></a>'
            "</main>"
        )
        main = doc.find("main")
        _apply_compound_figure_numbers(main, "test.html", "3")
        assert "Figure 3.1:" in doc.find("figcaption").get_text()
        assert doc.select("a")[0].string == "Figure 3.1"


class TestApplyCompoundTableNumbers:
    def test_numbers_tables_and_fills_refs(self):
        doc = _parse(
            "<main>"
            '<div id="t:tab1" data-caption="Cap"><table><tr><td>x</td></tr></table></div>'
            '<a href="#t:tab1"></a>'
            "</main>"
        )
        main = doc.find("main")
        _apply_compound_table_numbers(main, "test.html", "A")
        caption = doc.find("caption")
        assert caption is not None
        assert "Table A.1:" in caption.string
        assert doc.select("a")[0].string == "Table A.1"

"""Tests for mccole.util."""

import io
from pathlib import Path

from bs4 import BeautifulSoup

from mccole import util
from mccole.util import _get_slug_from_link, _load_order_section


class TestLoadLinks:
    def test_links_file_exists(self, src_dir):
        """load_links returns file content when links.md exists."""
        links = util.load_links(src_dir)
        assert "[link]: https://example.com" in links

    def test_links_file_missing(self, tmp_path):
        """load_links returns empty string when links.md is missing."""
        src = tmp_path / "no_extras"
        src.mkdir()
        links = util.load_links(src)
        assert links == ""


class TestLoadOrder:
    def test_loads_lessons_and_appendices(self, src_dir):
        """load_order returns lessons and appendices with correct numbering."""
        order = util.load_order(src_dir, Path("README.md"))
        assert len(order) == 2
        assert order["intro"]["number"] == "1"
        assert order["intro"]["kind"] == "lessons"
        assert order["refs"]["number"] == "A"
        assert order["refs"]["kind"] == "appendices"

    def test_previous_next_links(self, src_dir):
        """Entry dicts should have previous and next slugs."""
        order = util.load_order(src_dir, Path("README.md"))
        assert order["intro"]["previous"] is None
        assert order["intro"]["next"] == "refs"
        assert order["refs"]["previous"] == "intro"
        assert order["refs"]["next"] is None


class TestLoadSlides:
    def test_no_slides_div(self, src_dir):
        """Returns empty list when no slides div."""
        slides = util.load_slides(src_dir)
        assert slides == []

    def test_with_slides(self, tmp_path):
        """Returns slide entries from div#slides."""
        src = tmp_path / "site"
        src.mkdir()
        (src / "README.md").write_text(
            '<div id="slides">\n<a href="@/intro/slides.html">Slides</a>\n</div>\n',
            encoding="utf-8",
        )
        slides = util.load_slides(src)
        assert len(slides) == 1
        assert slides[0]["href"] == "@/intro/slides.html"
        assert slides[0]["title"] == "Slides"


class TestSlidesSrcFile:
    def test_converts_at_path(self, tmp_path):
        """Converts @/slug/slides.html to slug/slides.md."""
        src = tmp_path
        result = util.slides_src_file(src, "@/intro/slides.html")
        assert result == src / "intro" / "slides.md"


class TestGetSlugFromLink:
    def test_converts_at_link(self):
        assert _get_slug_from_link("@/intro/") == "intro"

    def test_converts_nested_link(self):
        assert _get_slug_from_link("@/glossary/") == "glossary"


class TestLoadOrderSection:
    def test_returns_slug_to_entry_dict(self):
        html = (
            '<div id="lessons">'
            '<ul><li><a href="@/intro/">Intro</a></li>'
            '<li><a href="@/adv/">Advanced</a></li></ul>'
            "</div>"
        )
        doc = BeautifulSoup(html, "html.parser")
        result = _load_order_section(doc, "lessons", lambda i: str(i + 1))
        assert set(result.keys()) == {"intro", "adv"}
        assert result["intro"]["number"] == "1"
        assert result["adv"]["number"] == "2"
        assert result["intro"]["kind"] == "lessons"
        assert result["intro"]["title"] == "Intro"


class TestWarn:
    def test_writes_to_stderr(self):
        """warn writes to stderr."""
        buf = io.StringIO()
        old_stderr = util.sys.stderr
        util.sys.stderr = buf
        try:
            util.warn("test message")
        finally:
            util.sys.stderr = old_stderr
        assert "test message" in buf.getvalue()

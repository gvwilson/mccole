"""Tests for mccole.build."""

import io
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

import mccole.build as build_mod
import mccole.util as util_mod
from mccole.build import (
    _build_index_page,
    _build_other,
    _build_page,
    _build_page_fragment,
    _collect_figure_numbers,
    _collect_table_numbers,
    _fill_element_numbers,
    _find_files,
    _fragment_patchers,
    _is_interesting_file,
    _load_book_repo,
    _load_book_title,
    _load_glossary,
    _make_context,
    _make_output_path,
    _make_root_prefix,
    _page_patchers,
    _patch_bibliography_links,
    _patch_exercise_labels,
    _patch_figure_numbers,
    _patch_glossary_links,
    _patch_markdown_attribute,
    _patch_pre_accessibility,
    _patch_pre_code_classes,
    _patch_root_links,
    _patch_table_numbers,
    _patch_terms_defined,
    _patch_th_scope,
    _patch_title,
    _render_page,
)


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def _capture_warn(func, *args, **kwargs):
    """Capture util.warn output during func call."""
    buf = io.StringIO()
    old = util_mod.sys.stderr
    util_mod.sys.stderr = buf
    try:
        result = func(*args, **kwargs)
    finally:
        util_mod.sys.stderr = old
    return result, buf.getvalue()


def _base_order():
    return {
        "intro": {
            "number": "1",
            "kind": "lessons",
            "title": "Intro",
            "previous": None,
            "next": None,
        },
        "refs": {
            "number": "A",
            "kind": "appendices",
            "title": "Refs",
            "previous": "intro",
            "next": None,
        },
    }


def _base_config(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "docs"
    src.mkdir(exist_ok=True)
    dst.mkdir(exist_ok=True)
    return {
        "src": src,
        "dst": dst,
        "home_page": Path("README.md"),
        "order": _base_order(),
        "links": "",
        "glossary": {},
        "slides": [],
        "brand": "Test",
        "book_repo": "",
        "book_title": "Test Book",
        "lang": "en",
        "extra_html": "",
        "forma": False,
        "math": False,
        "templates": tmp_path / "_templates",
        "extras": src / "_extras",
        "config": tmp_path / "pyproject.toml",
        "skip_names": set(),
        "skip_patterns": [],
        "verbose": 0,
    }


@pytest.fixture
def page_env(tmp_path):
    """Minimal Jinja2 environment with a page template."""
    tmpl_dir = tmp_path / "_templates"
    tmpl_dir.mkdir()
    (tmpl_dir / "page.html").write_text(
        "<html><head><title>test</title></head><body>{{ content }}</body></html>",
        encoding="utf-8",
    )
    return Environment(loader=FileSystemLoader(tmpl_dir))


@pytest.fixture
def page_config(tmp_path):
    """Minimal config with intro lesson source file present."""
    config = _base_config(tmp_path)
    intro_dir = config["src"] / "intro"
    intro_dir.mkdir()
    (intro_dir / "index.md").write_text("# Intro\n\nHello.\n", encoding="utf-8")
    config["order"]["intro"]["filepath"] = intro_dir / "index.md"
    config["order"]["refs"]["filepath"] = config["src"] / "refs" / "index.md"
    return config


class TestMakeRootPrefix:
    def test_depth_zero(self, tmp_path):
        config = {"dst": tmp_path / "docs"}
        path = tmp_path / "docs" / "index.html"
        assert _make_root_prefix(config, path) == "./"

    def test_depth_one(self, tmp_path):
        config = {"dst": tmp_path / "docs"}
        path = tmp_path / "docs" / "intro" / "index.html"
        assert _make_root_prefix(config, path) == "../"

    def test_depth_two(self, tmp_path):
        config = {"dst": tmp_path / "docs"}
        path = tmp_path / "docs" / "a" / "b" / "index.html"
        assert _make_root_prefix(config, path) == "../../"


class TestLoadBookTitle:
    def test_extracts_h1(self, tmp_path):
        (tmp_path / "README.md").write_text("# My Book\n\nContent.\n", encoding="utf-8")
        assert _load_book_title(tmp_path, Path("README.md")) == "My Book"

    def test_missing_h1_returns_empty(self, tmp_path):
        (tmp_path / "README.md").write_text("No heading here.\n", encoding="utf-8")
        assert _load_book_title(tmp_path, Path("README.md")) == ""

    def test_missing_file_returns_empty(self, tmp_path):
        assert _load_book_title(tmp_path, Path("MISSING.md")) == ""


class TestLoadBookRepo:
    def test_extracts_repo_link(self, tmp_path):
        (tmp_path / "README.md").write_text(
            "[repo]: https://github.com/x/y\n", encoding="utf-8"
        )
        assert _load_book_repo(tmp_path, Path("README.md")) == "https://github.com/x/y"

    def test_missing_link_returns_empty(self, tmp_path):
        (tmp_path / "README.md").write_text("# No repo\n", encoding="utf-8")
        assert _load_book_repo(tmp_path, Path("README.md")) == ""

    def test_missing_file_returns_empty(self, tmp_path):
        assert _load_book_repo(tmp_path, Path("MISSING.md")) == ""


class TestLoadGlossary:
    def test_extracts_ids_and_terms(self, tmp_path):
        gloss_dir = tmp_path / "glossary"
        gloss_dir.mkdir()
        (gloss_dir / "index.md").write_text(
            "<span id=\"term1\">Term One</span>\n:   Definition.\n",
            encoding="utf-8",
        )
        result = _load_glossary(tmp_path)
        assert result == {"term1": "Term One"}


class TestMakeOutputPath:
    def test_regular_file(self, tmp_path):
        config = {
            "dst": tmp_path / "docs",
            "home_page": Path("README.md"),
            "src": tmp_path / "src",
        }
        (tmp_path / "src" / "intro").mkdir(parents=True)
        src_path = tmp_path / "src" / "intro" / "index.md"
        result = _make_output_path(config, src_path, suffix=".html")
        assert result == tmp_path / "docs" / "intro" / "index.html"

    def test_standard_file(self, tmp_path):
        config = {
            "dst": tmp_path / "docs",
            "home_page": Path("README.md"),
            "src": tmp_path / "src",
        }
        (tmp_path / "src").mkdir(parents=True)
        src_path = tmp_path / "src" / "CODE_OF_CONDUCT.md"
        result = _make_output_path(config, src_path, suffix=".html")
        assert result == tmp_path / "docs" / "conduct" / "index.html"

    def test_home_page_non_standard(self, tmp_path):
        """Home page with a non-standard name maps to dst/index.html."""
        config = {
            "dst": tmp_path / "docs",
            "home_page": Path("main.md"),
            "src": tmp_path / "src",
        }
        (tmp_path / "src").mkdir(parents=True)
        src_path = tmp_path / "src" / "main.md"
        result = _make_output_path(config, src_path, suffix=".html")
        assert result == tmp_path / "docs" / "index.html"


class TestMakeContext:
    def test_with_slug(self, tmp_path):
        config = {
            **_base_config(tmp_path),
            "order": {
                "intro": {
                    "number": "1",
                    "kind": "lessons",
                    "title": "Intro",
                    "previous": None,
                    "next": "refs",
                },
                "refs": {
                    "number": "A",
                    "kind": "appendices",
                    "title": "Refs",
                    "previous": "intro",
                    "next": None,
                },
            },
        }
        ctx = _make_context(config, "intro")
        assert ctx["chapter_number"] == "1"
        assert ctx["chapter_kind"] == "lessons"
        assert ctx["prev"] == (None, None)
        assert ctx["next"] == ("refs", "Refs")

    def test_without_slug(self, tmp_path):
        config = _base_config(tmp_path)
        ctx = _make_context(config, None)
        assert ctx["chapter_number"] is None
        assert ctx["prev"] == (None, None)
        assert ctx["next"] == (None, None)


class TestFragmentAndPagePatchers:
    def test_fragment_patchers_returns_list(self):
        result = _fragment_patchers()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_page_patchers_returns_list(self):
        result = _page_patchers()
        assert isinstance(result, list)
        assert len(result) > 0


class TestCollectFigureNumbers:
    def test_numbers_figure_and_updates_caption(self, tmp_path):
        doc = _soup(
            '<figure id="f:fig1"><figcaption>caption</figcaption></figure>'
        )
        known = _collect_figure_numbers(tmp_path / "test.html", doc)
        assert known == {"f:fig1": 1}
        assert "Figure 1:" in doc.find("figcaption").get_text()

    def test_figure_missing_id_skipped(self, tmp_path):
        doc = _soup("<figure><figcaption>no id</figcaption></figure>")
        _, err = _capture_warn(_collect_figure_numbers, tmp_path / "test.html", doc)
        assert "no ID" in err

    def test_figure_bad_id_prefix_skipped(self, tmp_path):
        doc = _soup('<figure id="bad:fig1"><figcaption>x</figcaption></figure>')
        _, err = _capture_warn(_collect_figure_numbers, tmp_path / "test.html", doc)
        assert "does not start with" in err

    def test_figure_missing_figcaption_skipped(self, tmp_path):
        doc = _soup('<figure id="f:fig1"></figure>')
        _, err = _capture_warn(_collect_figure_numbers, tmp_path / "test.html", doc)
        assert "missing/too many figcaption" in err


class TestCollectTableNumbers:
    def test_numbers_table_and_inserts_caption(self, tmp_path):
        doc = _soup(
            '<div id="t:tab1" data-caption="My table">'
            "<table><tr><td>x</td></tr></table>"
            "</div>"
        )
        known = _collect_table_numbers(tmp_path / "test.html", doc)
        assert known == {"t:tab1": 1}
        assert "Table 1: My table" in doc.find("caption").get_text()

    def test_table_missing_data_caption_skipped(self, tmp_path):
        doc = _soup('<div id="t:tab1"><table><tr><td>y</td></tr></table></div>')
        _, err = _capture_warn(_collect_table_numbers, tmp_path / "test.html", doc)
        assert "no data-caption" in err

    def test_table_missing_inner_table_skipped(self, tmp_path):
        doc = _soup('<div id="t:tab1" data-caption="x"></div>')
        _, err = _capture_warn(_collect_table_numbers, tmp_path / "test.html", doc)
        assert "missing/too many tables" in err


class TestFillElementNumbers:
    def test_known_ref_filled(self, tmp_path):
        doc = _soup('<a href="#f:fig1">?</a>')
        _fill_element_numbers(tmp_path / "test.html", doc, "#f:", {"f:fig1": 1}, "Figure")
        assert doc.find("a").string == "Figure 1"

    def test_unknown_ref_warns(self, tmp_path):
        doc = _soup('<a href="#f:missing">?</a>')
        _, err = _capture_warn(
            _fill_element_numbers, tmp_path / "test.html", doc, "#f:", {}, "Figure"
        )
        assert "unknown cross-reference" in err


class TestIsInterestingFile:
    def test_regular_file_is_interesting(self, tmp_path):
        cfg = tmp_path / "pyproject.toml"
        cfg.write_text("[tool]\n", encoding="utf-8")
        f = tmp_path / "style.css"
        f.write_text("body {}\n", encoding="utf-8")
        assert _is_interesting_file({"config": cfg}, set(), [], f) is True

    def test_excluded_file_not_interesting(self, tmp_path):
        cfg = tmp_path / "pyproject.toml"
        cfg.write_text("[tool]\n", encoding="utf-8")
        f = tmp_path / "style.css"
        f.write_text("body {}\n", encoding="utf-8")
        assert _is_interesting_file({"config": cfg}, {f}, [], f) is False

    def test_config_file_not_interesting(self, tmp_path):
        cfg = tmp_path / "pyproject.toml"
        cfg.write_text("[tool]\n", encoding="utf-8")
        assert _is_interesting_file({"config": cfg}, set(), [], cfg) is False

    def test_skip_pattern_not_interesting(self, tmp_path):
        cfg = tmp_path / "pyproject.toml"
        cfg.write_text("[tool]\n", encoding="utf-8")
        f = tmp_path / "file.log"
        f.write_text("log\n", encoding="utf-8")
        assert _is_interesting_file({"config": cfg}, set(), ["*.log"], f) is False


class TestBuildOther:
    def test_copies_file(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "docs"
        src.mkdir()
        dst.mkdir()
        f = src / "style.css"
        f.write_text("body {}\n", encoding="utf-8")
        config = {
            "src": src,
            "dst": dst,
            "home_page": Path("README.md"),
        }
        _build_other(config, f)
        assert (dst / "style.css").read_text(encoding="utf-8") == "body {}\n"


class TestPatchMarkdownAttribute:
    def test_removes_markdown_attribute(self):
        doc = _soup('<div markdown="1"><p>text</p></div>')
        _patch_markdown_attribute({}, Path("src.md"), Path("dst.html"), doc)
        assert doc.find("div").get("markdown") is None


class TestPatchExerciseLabels:
    def test_adds_aria_label(self):
        doc = _soup('<section class="exercises"><p>ex</p></section>')
        _patch_exercise_labels({}, Path("src.md"), Path("dst.html"), doc)
        assert doc.find("section")["aria-label"] == "Exercises"

    def test_preserves_existing_aria_label(self):
        doc = _soup('<section class="exercises" aria-label="Custom">x</section>')
        _patch_exercise_labels({}, Path("src.md"), Path("dst.html"), doc)
        assert doc.find("section")["aria-label"] == "Custom"


class TestPatchPreAccessibility:
    def test_adds_tabindex(self):
        doc = _soup("<pre>code</pre>")
        _patch_pre_accessibility({}, Path("src.md"), Path("dst.html"), doc)
        assert doc.find("pre")["tabindex"] == "0"

    def test_extracts_language_class(self):
        doc = _soup('<pre class="language-python">code</pre>')
        _patch_pre_accessibility({}, Path("src.md"), Path("dst.html"), doc)
        assert doc.find("pre")["data-lang"] == "python"

    def test_no_language_class_no_data_lang(self):
        doc = _soup('<pre class="other">code</pre>')
        _patch_pre_accessibility({}, Path("src.md"), Path("dst.html"), doc)
        assert doc.find("pre").get("data-lang") is None


class TestPatchPreCodeClasses:
    def test_copies_code_class_to_pre(self):
        doc = _soup('<pre><code class="language-python">x</code></pre>')
        _patch_pre_code_classes({}, Path("src.md"), Path("dst.html"), doc)
        assert "language-python" in doc.find("pre").get("class", [])


class TestPatchThScope:
    def test_adds_col_scope_to_thead_th(self):
        doc = _soup("<table><thead><tr><th>H</th></tr></thead></table>")
        _patch_th_scope({}, Path("src.md"), Path("dst.html"), doc)
        assert doc.find("thead").find("th")["scope"] == "col"

    def test_adds_row_scope_to_tbody_th(self):
        doc = _soup("<table><tbody><tr><th>R</th><td>x</td></tr></tbody></table>")
        _patch_th_scope({}, Path("src.md"), Path("dst.html"), doc)
        assert doc.find("tbody").find("th")["scope"] == "row"

    def test_preserves_existing_scope(self):
        doc = _soup('<table><thead><tr><th scope="row">H</th></tr></thead></table>')
        _patch_th_scope({}, Path("src.md"), Path("dst.html"), doc)
        assert doc.find("thead").find("th")["scope"] == "row"


class TestPatchRootLinks:
    def test_rewrites_at_links(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        config = {"dst": docs}
        dst_path = docs / "intro" / "index.html"
        doc = _soup('<a href="@/glossary/#x">link</a>')
        _patch_root_links(config, Path("src.md"), dst_path, doc)
        assert doc.find("a")["href"] == "../glossary/#x"

    def test_leaves_external_links(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        config = {"dst": docs}
        dst_path = docs / "index.html"
        doc = _soup('<a href="https://example.com">link</a>')
        _patch_root_links(config, Path("src.md"), dst_path, doc)
        assert doc.find("a")["href"] == "https://example.com"


class TestPatchBibliographyLinks:
    def test_rewrites_bib_link(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        config = {"dst": docs}
        dst_path = docs / "intro" / "index.html"
        doc = _soup('<a href="b:Key2020">text</a>')
        _patch_bibliography_links(config, Path("src.md"), dst_path, doc)
        assert doc.find("a")["href"] == "../bibliography/#Key2020"
        assert doc.find("a").string == "Key2020"


class TestPatchGlossaryLinks:
    def test_rewrites_glossary_link_without_changing_text(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        config = {"dst": docs}
        dst_path = docs / "intro" / "index.html"
        doc = _soup('<a href="g:term1">the term</a>')
        _patch_glossary_links(config, Path("src.md"), dst_path, doc)
        assert doc.find("a")["href"] == "../glossary/#term1"
        assert doc.find("a").string == "the term"


class TestPatchFigureNumbers:
    def test_numbers_figure_and_fills_ref(self, tmp_path):
        dst_path = tmp_path / "test.html"
        doc = _soup(
            '<figure id="f:fig1"><figcaption>desc</figcaption></figure>'
            '<a href="#f:fig1">?</a>'
        )
        _patch_figure_numbers({}, Path("src.md"), dst_path, doc)
        assert "Figure 1:" in doc.find("figcaption").get_text()
        assert doc.find("a").string == "Figure 1"


class TestPatchTableNumbers:
    def test_numbers_table_and_fills_ref(self, tmp_path):
        dst_path = tmp_path / "test.html"
        doc = _soup(
            '<div id="t:tab1" data-caption="Cap"><table><tr><td>x</td></tr></table></div>'
            '<a href="#t:tab1">?</a>'
        )
        _patch_table_numbers({}, Path("src.md"), dst_path, doc)
        assert "Table 1: Cap" in doc.find("caption").get_text()
        assert doc.find("a").string == "Table 1"


class TestPatchTermsDefined:
    def test_no_terms_paragraph_is_noop(self):
        doc = _soup("<p>no terms here</p>")
        _patch_terms_defined({"glossary": {}}, Path("src.md"), Path("dst.html"), doc)
        assert doc.find("p") is not None

    def test_empty_terms_paragraph_removed(self):
        doc = _soup('<p id="terms">placeholder</p>')
        _patch_terms_defined({"glossary": {}}, Path("src.md"), Path("dst.html"), doc)
        assert doc.find("p", id="terms") is None

    def test_terms_paragraph_populated(self):
        doc = _soup('<p id="terms">placeholder</p><a href="g:term1">x</a>')
        config = {"glossary": {"term1": "Term One"}}
        _patch_terms_defined(config, Path("src.md"), Path("dst.html"), doc)
        p = doc.find("p", id="terms")
        assert p is not None
        assert "Terms defined:" in p.get_text()
        assert "Term One" in p.get_text()

    def test_multiple_terms_paragraphs_warns(self, tmp_path):
        doc = _soup('<p id="terms">a</p><p id="terms">b</p>')
        _, err = _capture_warn(
            _patch_terms_defined, {"glossary": {}}, Path("src.md"), Path("dst.html"), doc
        )
        assert "multiple p#terms" in err


class TestPatchTitle:
    def test_sets_title_from_h1(self):
        doc = _soup("<html><head><title>Old</title></head><body><h1>New</h1></body></html>")
        _patch_title({"slides": []}, Path("src.md"), Path("dst.html"), doc)
        assert doc.title.string == "New"

    def test_warns_when_no_h1(self, tmp_path):
        doc = _soup("<html><head><title>T</title></head><body><p>no h1</p></body></html>")
        _, err = _capture_warn(
            _patch_title, {"slides": []}, Path("src.md"), Path("dst.html"), doc
        )
        assert "lacks H1 heading" in err

    def test_warns_when_no_title_element(self, tmp_path):
        doc = _soup("<html><head></head><body><h1>Hi</h1></body></html>")
        _, err = _capture_warn(
            _patch_title, {"slides": []}, Path("src.md"), Path("dst.html"), doc
        )
        assert "does not have <title>" in err

    def test_slides_file_no_h1_warning(self, tmp_path):
        """Source files that are slides pages don't warn for missing H1."""
        src_path = tmp_path / "slides.md"
        doc = _soup("<html><head><title>T</title></head><body><p>slides</p></body></html>")
        config = {"slides": [{"src_file": src_path}]}
        _, err = _capture_warn(_patch_title, config, src_path, Path("dst.html"), doc)
        assert "lacks H1 heading" not in err


class TestFindFiles:
    def test_returns_slugs_and_others(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "docs"
        src.mkdir()
        dst.mkdir()
        (src / "README.md").write_text("# Book\n", encoding="utf-8")
        (src / "intro").mkdir()
        intro_md = src / "intro" / "index.md"
        intro_md.write_text("# Intro\n", encoding="utf-8")
        extra = src / "style.css"
        extra.write_text("body {}\n", encoding="utf-8")
        cfg = tmp_path / "pyproject.toml"
        cfg.write_text("[tool]\n", encoding="utf-8")

        config = {
            "src": src,
            "dst": dst,
            "home_page": Path("README.md"),
            "order": {"intro": {"filepath": intro_md}},
            "extras": src / "_extras",
            "templates": src / "_templates",
            "slides": [],
            "skip_names": set(),
            "skip_patterns": [],
            "config": cfg,
        }
        slugs, others = _find_files(config)
        assert "intro" in slugs
        assert extra in others
        assert intro_md not in others


class TestRenderPage:
    def test_writes_rendered_html(self, tmp_path, page_env, page_config):
        dst_path = page_config["dst"] / "intro" / "index.html"
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        _render_page(
            page_config,
            page_env,
            "intro",
            page_config["src"] / "intro" / "index.md",
            dst_path,
            "<p>Hello</p>",
            {},
            "page.html",
        )
        assert dst_path.exists()
        assert "<p>Hello</p>" in dst_path.read_text(encoding="utf-8")


class TestBuildPageFragment:
    def test_returns_metadata_path_doc(self, tmp_path, page_env, page_config):
        metadata, dst_path, doc = _build_page_fragment(
            page_config,
            page_env,
            "intro",
            page_config["src"] / "intro" / "index.md",
        )
        assert isinstance(metadata, dict)
        assert dst_path.suffix == ".html"
        assert doc is not None


class TestBuildPage:
    def test_writes_html_file(self, tmp_path, page_env, page_config):
        _build_page(
            page_config,
            page_env,
            "intro",
            page_config["src"] / "intro" / "index.md",
        )
        dst_path = page_config["dst"] / "intro" / "index.html"
        assert dst_path.exists()


class TestBuildIndexPage:
    def test_writes_index_html(self, tmp_path, page_env, page_config):
        idx_src = page_config["src"] / "index" / "index.md"
        idx_src.parent.mkdir()
        idx_src.write_text("# Index\n", encoding="utf-8")
        page_config["order"]["index"] = {
            "number": "",
            "kind": "lessons",
            "title": "Index",
            "previous": None,
            "next": None,
            "filepath": idx_src,
        }
        entries = [
            {"key": "apple", "text": "Apple", "slug": "intro", "uid": "ix-intro-1"}
        ]
        _build_index_page(page_config, page_env, entries)
        dst_path = page_config["dst"] / "index" / "index.html"
        assert dst_path.exists()

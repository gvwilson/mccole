"""Test site checker."""

import argparse
import re

from bs4 import BeautifulSoup
import pytest

from mccole.build import main as build, construct_parser as build_parser
from mccole.lint import main as lint, construct_parser as lint_parser
from .conftest import make_fs

DIV_APPENDICES = re.compile(r'<div id="appendices">.+?</div>', re.DOTALL)
NAV_LESSONS = re.compile('<span class="dropdown-content" id="nav-lessons">.+?</span>', re.DOTALL)

MINIMAL_GLOSSARY_REFS = """
# Title

[first](g:first)
[second](g:second)
"""


@pytest.fixture
def lint_fs(build_opt, bare_fs):
    make_fs(
        {
            bare_fs / "bibliography" / "index.md": "# Bibliography",
        }
    )
    return bare_fs


def test_construct_parser_with_default_values():
    parser = argparse.ArgumentParser()
    lint_parser(parser)
    opt = parser.parse_args([])
    assert hasattr(opt, "dst")


def test_no_problems_to_report(build_opt, lint_opt, lint_fs, capsys):
    make_fs(
        {
            lint_fs / build_opt.src / "test.md": MINIMAL_GLOSSARY_REFS,
        }
    )
    build(build_opt)
    output_path = lint_fs / build_opt.dst / "test.html"
    lint(lint_opt)
    captured = capsys.readouterr()
    assert not captured.err


def test_multiple_h1_in_file(build_opt, lint_opt, lint_fs, capsys):
    make_fs(
        {
            lint_fs / "test.md": "# First\n\n# Second\n",
        }
    )
    build(build_opt)
    lint(lint_opt)
    captured = capsys.readouterr()
    m = re.search(r"(\d) H1 elements found", captured.err)
    assert m and int(m.group(1)) == 2


@pytest.mark.parametrize("kind", ["bibliography", "glossary"])
def test_special_file_not_found(build_opt, lint_opt, lint_fs, capsys, kind):
    build(build_opt)
    (lint_fs / lint_opt.dst / kind / "index.html").unlink()
    lint(lint_opt)
    captured = capsys.readouterr()
    assert re.search(f"{kind}/index.html not found", captured.err)


@pytest.mark.parametrize("kind,key", [["bibliography", "b:key"], ["glossary", "g:key"]])
def test_special_key_undefined(build_opt, lint_opt, lint_fs, capsys, kind, key):
    text = f"""\
# A
[]({key})
"""
    make_fs(
        {
            lint_fs / "a.md": text,
        }
    )

    build(build_opt)
    lint(lint_opt)

    captured = capsys.readouterr()
    assert re.search(f"unknown {kind} keys in .+: key", captured.err)


@pytest.mark.parametrize("kind", ["bibliography", "glossary"])
def test_special_key_unused(build_opt, lint_opt, lint_fs, capsys, kind):
    build(build_opt)

    text = """\
# Title
<main>
<span id="key">text</span>
</main>
"""
    make_fs(
        {
            lint_fs / lint_opt.dst / kind / "index.html": text,
        }
    )

    lint(lint_opt)

    captured = capsys.readouterr()
    assert re.search(f"unused {kind} keys: key", captured.err)


def test_multiple_main_in_special_file(build_opt, lint_opt, lint_fs, capsys):
    build(build_opt)
    page = build_opt.dst / "bibliography" / "index.html"
    content = page.read_text()
    content = content.replace("<main>", "<main></main><main>")
    page.write_text(content)

    lint(lint_opt)
    captured = capsys.readouterr()
    assert "missing or multiple" in captured.err


def test_glossary_term_redefined(build_opt, lint_opt, lint_fs, capsys):
    a = """\
# A
[term 1](g:term_1)
[term 1 again](g:term_1)
[term 2](g:term_2)
"""
    b = """\
# B
[term 2](g:term_2)
"""
    g = """\
# Glossary
<span id="term_1">term 1</span>
<span id="term_2">term 2</span>
"""
    make_fs(
        {
            lint_fs / "a.md": a,
            lint_fs / "b.md": b,
            lint_fs / "glossary" / "index.md": g,
        }
    )

    build(build_opt)
    lint(lint_opt)

    captured = capsys.readouterr()
    assert re.search(r"glossary entry 'term_1' defined in .+, .+", captured.err)
    assert re.search(r"glossary entry 'term_2' defined in .+, .+", captured.err)


def test_glossary_key_unused(build_opt, lint_opt, lint_fs, capsys):
    build(build_opt)

    g = """\
# Glossary
<main>
<span id="key">text</span>
</main>
"""
    make_fs(
        {
            lint_fs / lint_opt.dst / "glossary" / "index.html": g,
        }
    )

    lint(lint_opt)

    captured = capsys.readouterr()
    assert re.search("unused glossary keys: key", captured.err)


@pytest.mark.parametrize(
    "headings,msg",
    [
        ["", "has missing/multiple heading(s)"],
        ["## first\n## second", "has missing/multiple heading(s)"],
        ["# level 1", "has h1 instead of h3"],
        ["## level 2", "has h2 instead of h3"],
        ["#### level 4", "has h4 instead of h3"],
    ],
)
def test_exercise_section_has_bad_headings(
    build_opt, lint_opt, lint_fs, capsys, headings, msg
):
    text = f"""\
# Title
<section class="exercise" markdown="1">
{headings}
</section>
"""
    make_fs(
        {
            lint_fs / build_opt.src / "test.md": text,
        }
    )

    build(build_opt)
    lint(lint_opt)

    captured = capsys.readouterr()
    assert msg in captured.err


def test_html_validation_with_valid_html(build_opt, lint_opt, lint_fs, capsys):
    make_fs(
        {
            lint_fs / build_opt.src / "test.md": MINIMAL_GLOSSARY_REFS,
        }
    )
    build(build_opt)
    lint_opt.html = True
    lint(lint_opt)
    captured = capsys.readouterr()
    assert not captured.err


def test_html_validation_with_invalid_html(build_opt, lint_opt, lint_fs, capsys):
    build(build_opt)
    page = build_opt.dst / "index.html"
    content = page.read_text()
    page.write_text(content.replace('<html lang="en">', ""))

    lint_opt.html = True
    lint(lint_opt)
    captured = capsys.readouterr()
    assert captured.out


@pytest.mark.parametrize(
    "pattern,replacement",
    [
        [NAV_LESSONS, ""],
        [DIV_APPENDICES, ""],
    ],
)
def test_compare_template_readme_missing_nav(
    build_opt, lint_opt, lint_fs, capsys, pattern, replacement
):
    build(build_opt)
    page = build_opt.dst / "index.html"
    content = page.read_text()
    content = pattern.sub(replacement, content)
    page.write_text(content)

    lint(lint_opt)
    captured = capsys.readouterr()
    assert "missing or multiple" in captured.err


def test_compare_template_readme_mismatch_titles(build_opt, lint_opt, lint_fs, capsys):
    build(build_opt)
    page = build_opt.dst / "index.html"
    content = page.read_text()
    content = content.replace(
        '<span id="nav-lessons" class="dropdown-content"></span>',
        '<span id="nav-lessons" class="dropdown-content"><a href="./01_intro/">Introduction</a></span>',
    )
    content = content.replace(
        '<div id="lessons"></div>',
        '<div id="lessons"><li><a href="./01_intro/">Not Introduction</a></li></div>',
    )
    page.write_text(content)

    lint(lint_opt)
    captured = capsys.readouterr()
    assert "mis-match in README and nav paths" in captured.err


def test_figure_missing_id(build_opt, lint_opt, lint_fs, capsys):
    text = """\
# Title
<figure>
<figcaption>Figure 1: A caption</figcaption>
</figure>
"""
    make_fs(
        {
            lint_fs / build_opt.src / "test.md": text,
        }
    )
    build(build_opt)
    lint(lint_opt)
    captured = capsys.readouterr()
    assert "figure missing 'id'" in captured.err


def test_figure_missing_caption(build_opt, lint_opt, lint_fs, capsys):
    text = """\
# Title
<figure id="f:test">
</figure>
"""
    make_fs(
        {
            lint_fs / build_opt.src / "test.md": text,
        }
    )
    build(build_opt)
    lint(lint_opt)
    captured = capsys.readouterr()
    assert "figure missing/extra caption" in captured.err


def test_figure_has_multiple_captions(build_opt, lint_opt, lint_fs, capsys):
    text = """\
# Title
<figure id="f:test">
<figcaption>Figure 1: First caption</figcaption>
<figcaption>Figure 1: Second caption</figcaption>
</figure>
"""
    make_fs(
        {
            lint_fs / build_opt.src / "test.md": text,
        }
    )
    build(build_opt)
    lint(lint_opt)
    captured = capsys.readouterr()
    assert "figure missing/extra caption" in captured.err


def test_figure_badly_formatted_caption(build_opt, lint_opt, lint_fs, capsys):
    build(build_opt)
    html_content = """\
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
<main>
<figure id="f:test">
<figcaption>Bad caption format</figcaption>
</figure>
</main>
</body>
</html>
"""
    make_fs(
        {
            lint_fs / lint_opt.dst / "test.html": html_content,
        }
    )
    lint(lint_opt)
    captured = capsys.readouterr()
    assert "badly-formatted figure caption 'Bad caption format'" in captured.err


def test_table_missing_id(build_opt, lint_opt, lint_fs, capsys):
    build(build_opt)
    html_content = """\
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
<main>
<div data-table-caption="Table Title">
<table>
<tr><td>data</td></tr>
</table>
</div>
</main>
</body>
</html>
"""
    make_fs(
        {
            lint_fs / lint_opt.dst / "test.html": html_content,
        }
    )
    lint(lint_opt)
    captured = capsys.readouterr()
    assert "table div missing 'data-table-id'" in captured.err


def test_table_wrong_id_prefix(build_opt, lint_opt, lint_fs, capsys):
    build(build_opt)
    html_content = """\
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
<main>
<div data-table-id="wrong:test" data-table-caption="Table Title">
<table>
<tr><td>data</td></tr>
</table>
</div>
</main>
</body>
</html>
"""
    make_fs(
        {
            lint_fs / lint_opt.dst / "test.html": html_content,
        }
    )
    lint(lint_opt)
    captured = capsys.readouterr()
    assert "does not start with 't:'" in captured.err


def test_table_missing_caption(build_opt, lint_opt, lint_fs, capsys):
    build(build_opt)
    html_content = """\
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
<main>
<div data-table-id="t:test">
<table>
<tr><td>data</td></tr>
</table>
</div>
</main>
</body>
</html>
"""
    make_fs(
        {
            lint_fs / lint_opt.dst / "test.html": html_content,
        }
    )
    lint(lint_opt)
    captured = capsys.readouterr()
    assert "table div missing 'data-table-caption'" in captured.err


def test_table_no_table_element(build_opt, lint_opt, lint_fs, capsys):
    build(build_opt)
    html_content = """\
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
<main>
<div data-table-id="t:test" data-table-caption="Table Title">
<p>Not a table</p>
</div>
</main>
</body>
</html>
"""
    make_fs(
        {
            lint_fs / lint_opt.dst / "test.html": html_content,
        }
    )
    lint(lint_opt)
    captured = capsys.readouterr()
    assert "table div should contain exactly one table, found 0" in captured.err


def test_table_multiple_table_elements(build_opt, lint_opt, lint_fs, capsys):
    build(build_opt)
    html_content = """\
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
<main>
<div data-table-id="t:test" data-table-caption="Table Title">
<table><tr><td>first</td></tr></table>
<table><tr><td>second</td></tr></table>
</div>
</main>
</body>
</html>
"""
    make_fs(
        {
            lint_fs / lint_opt.dst / "test.html": html_content,
        }
    )
    lint(lint_opt)
    captured = capsys.readouterr()
    assert "table div should contain exactly one table, found 2" in captured.err


def test_link_in_page_body_resolves(build_opt, lint_opt, lint_fs, capsys):
    markdown_content = (
        MINIMAL_GLOSSARY_REFS
        + """\

[text][url]

[url]: http://something
"""
    )
    make_fs(
        {
            lint_fs / lint_opt.src / "test.md": markdown_content,
        }
    )
    build(build_opt)
    lint(lint_opt)
    captured = capsys.readouterr()
    assert not captured.err


def test_unresolved_link_in_page_body(build_opt, lint_opt, lint_fs, capsys):
    markdown_content = (
        MINIMAL_GLOSSARY_REFS
        + """\

[text][url]
"""
    )
    make_fs(
        {
            lint_fs / lint_opt.src / "test.md": markdown_content,
        }
    )
    build(build_opt)
    lint(lint_opt)
    captured = capsys.readouterr()
    assert "undefined link reference(s)" in captured.err


def test_link_in_external_links(build_opt, lint_opt, lint_fs, capsys):
    markdown_content = (
        MINIMAL_GLOSSARY_REFS
        + """\

[text][url]
"""
    )
    links_content = """\
[url]: http://something
"""
    links_path = lint_fs / lint_opt.src / "links.txt"
    make_fs(
        {
            lint_fs / lint_opt.src / "test.md": markdown_content,
            links_path: links_content,
        }
    )
    build(build_opt)
    lint_opt.links = links_path
    lint(lint_opt)
    captured = capsys.readouterr()
    assert not captured.err


def test_unused_internal_link_definition(build_opt, lint_opt, lint_fs, capsys):
    markdown_content = (
        MINIMAL_GLOSSARY_REFS
        + """\

[url]: http://something
"""
    )
    make_fs(
        {
            lint_fs / lint_opt.src / "test.md": markdown_content,
        }
    )
    build(build_opt)
    lint(lint_opt)
    captured = capsys.readouterr()
    assert "unused link definition(s)" in captured.err


def test_unused_global_link_definition(build_opt, lint_opt, lint_fs, capsys):
    links_content = """\
[url]: http://something
"""
    links_path = lint_fs / lint_opt.src / "links.txt"
    make_fs(
        {
            lint_fs / lint_opt.src / "test.md": MINIMAL_GLOSSARY_REFS,
            links_path: links_content,
        }
    )
    build(build_opt)
    lint_opt.links = links_path
    lint(lint_opt)
    captured = capsys.readouterr()
    assert "unused global link definition(s)" in captured.err

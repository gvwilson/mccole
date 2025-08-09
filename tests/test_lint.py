"""Test site checker."""

import argparse
import re

from bs4 import BeautifulSoup
import pytest

from mccole.build import build, construct_parser as build_parser
from mccole.lint import lint, construct_parser as lint_parser

DIV_APPENDICES = '<div id="appendices"></div>'
NAV_LESSONS = '<span class="dropdown-content" id="nav-lessons"></span>'

README = """\
# README
<div id="syllabus"></div>
<div id="appendices"></div>
"""


@pytest.fixture
def lint_fs(build_opt, bare_fs):
    (bare_fs / "README.md").write_text(README)
    (bare_fs / "bibliography").mkdir()
    (bare_fs / "bibliography" / "index.md").write_text("# Bibliography")
    (bare_fs / "glossary").mkdir()
    (bare_fs / "glossary" / "index.md").write_text("# Glossary")
    return bare_fs


def test_lint_construct_parser_with_default_values():
    parser = argparse.ArgumentParser()
    lint_parser(parser)
    opt = parser.parse_args([])
    assert hasattr(opt, "dst")


def test_lint_no_problems_to_report(build_opt, lint_opt, lint_fs, capsys):
    build(build_opt)
    lint(lint_opt)
    captured = capsys.readouterr()
    assert not captured.err


def test_lint_multiple_h1_in_file(build_opt, lint_opt, lint_fs, capsys):
    (lint_fs / "test.md").write_text("# First\n\n# Second\n")
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
    lines = [
        "# A",
        f"[]({key})",
    ]
    (lint_fs / "a.md").write_text("\n".join(lines))

    build(build_opt)
    lint(lint_opt)

    captured = capsys.readouterr()
    assert re.search(f"unknown {kind} keys in .+: key", captured.err)


@pytest.mark.parametrize("kind", ["bibliography", "glossary"])
def test_special_key_unused(build_opt, lint_opt, lint_fs, capsys, kind):
    build(build_opt)

    lines = [
        "# Title",
        "<main>",
        '<span id="key">text</span>',
        "</main>",
    ]
    (lint_fs / lint_opt.dst / kind / "index.html").write_text("\n".join(lines))

    lint(lint_opt)

    captured = capsys.readouterr()
    assert re.search(f"unused {kind} keys: key", captured.err)


def test_multiple_main_in_special_file(build_opt, lint_opt, lint_fs, capsys):
    build(build_opt)
    page = (build_opt.dst / "bibliography" / "index.html")
    content = page.read_text()
    content = content.replace("<main>", "<main></main><main>")
    page.write_text(content)

    lint(lint_opt)
    captured = capsys.readouterr()
    assert "missing or multiple" in captured.err


def test_glossary_term_redefined(build_opt, lint_opt, lint_fs, capsys):
    a = [
        "# A",
        "[term 1](g:term_1)",
        "[term 1 again](g:term_1)",
        "[term 2](g:term_2)",
    ]
    (lint_fs / "a.md").write_text("\n".join(a))

    b = [
        "# B",
        "[term 2](g:term_2)",
    ]
    (lint_fs / "b.md").write_text("\n".join(b))

    g = [
        "# Glossary",
        '<span id="term_1">term 1</span>',
        '<span id="term_2">term 2</span>',
    ]
    (lint_fs / "glossary" / "index.md").write_text("\n".join(g))

    build(build_opt)
    lint(lint_opt)

    captured = capsys.readouterr()
    assert re.search(r"glossary entry 'term_1' defined in .+, .+", captured.err)
    assert re.search(r"glossary entry 'term_2' defined in .+, .+", captured.err)


def test_glossary_key_unused(build_opt, lint_opt, lint_fs, capsys):
    build(build_opt)

    g = [
        "# Glossary",
        "<main>",
        '<span id="key">text</span>',
        "</main>",
    ]
    (lint_fs / lint_opt.dst / "glossary" / "index.html").write_text("\n".join(g))

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
    lines = [
        "# Title",
        '<section class="exercise" markdown="1">',
        headings,
        "</section>",
    ]
    (lint_fs / build_opt.src / "test.md").write_text("\n".join(lines))

    build(build_opt)
    lint(lint_opt)

    captured = capsys.readouterr()
    assert msg in captured.err


def test_html_validation_with_valid_html(build_opt, lint_opt, lint_fs, capsys):
    build(build_opt)
    lint_opt.html = True
    lint(lint_opt)
    captured = capsys.readouterr()
    assert not captured.err


def test_html_validation_with_invalid_html(build_opt, lint_opt, lint_fs, capsys):
    build(build_opt)
    page = (build_opt.dst / "index.html")
    content = page.read_text()
    page.write_text(content.replace('<html lang="en">', ""))

    lint_opt.html = True
    lint(lint_opt)
    captured = capsys.readouterr()
    assert captured.out


@pytest.mark.parametrize("target,replacement", [
    [NAV_LESSONS, ""],
    [NAV_LESSONS, f"{NAV_LESSONS}\n{NAV_LESSONS}"],
    [DIV_APPENDICES, ""],
    [DIV_APPENDICES, f"{DIV_APPENDICES}\n{DIV_APPENDICES}"],
])
def test_compare_template_readme_missing_nav(build_opt, lint_opt, lint_fs, capsys,target, replacement):
    build(build_opt)
    page = (build_opt.dst / "index.html")
    content = page.read_text()
    content = content.replace(target, replacement)
    page.write_text(content)

    lint_opt.html = True
    lint(lint_opt)
    captured = capsys.readouterr()
    assert "missing or multiple" in captured.err

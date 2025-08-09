"""Test that sites build."""

import argparse

from bs4 import BeautifulSoup
import pytest

from mccole.build import build, construct_parser, _load_glossary


def test_build_construct_parser_with_default_values():
    parser = argparse.ArgumentParser()
    construct_parser(parser)
    opt = parser.parse_args([])
    assert all(hasattr(opt, key) for key in ["config", "dst", "src", "templates"])


def test_build_with_no_files_creates_empty_output_directory(bare_fs, build_opt):
    build(build_opt)
    dst = bare_fs / build_opt.dst
    assert dst.is_dir()
    assert len(list(dst.iterdir())) == 0


def test_build_with_single_plain_markdown_file_creates_one_output_file(
    bare_fs, build_opt
):
    (bare_fs / build_opt.src / "test.md").write_text("# Title\nbody")
    build(build_opt)
    expected = bare_fs / build_opt.dst / "test.html"
    assert expected.is_file()
    doc = BeautifulSoup(expected.read_text(), "html.parser")
    assert doc.title.string == "Title"
    paragraphs = doc.find_all("p")
    assert len(paragraphs) == 1 and paragraphs[0].string == "body"


def test_build_does_not_copy_dot_files(bare_fs, build_opt):
    (bare_fs / build_opt.src / ".gitignore").write_text("content")
    build(build_opt)
    assert len(list((bare_fs / build_opt.dst).iterdir())) == 0


def test_build_does_not_copy_dot_dirs(bare_fs, build_opt):
    (bare_fs / build_opt.src / ".settings").mkdir()
    build(build_opt)
    assert len(list((bare_fs / build_opt.dst).iterdir())) == 0


def test_build_does_not_copy_symlinks(bare_fs, build_opt):
    (bare_fs / build_opt.src / "link.lnk").symlink_to("/tmp")
    build(build_opt)
    assert len(list((bare_fs / build_opt.dst).iterdir())) == 0


def test_build_does_not_copy_destination_files(bare_fs, build_opt):
    (bare_fs / build_opt.dst).mkdir()
    (bare_fs / build_opt.dst / "existing.html").write_text("<html></html>")
    build(build_opt)
    assert len(list((bare_fs / build_opt.dst).iterdir())) == 1


def test_build_does_not_copy_explicitly_skipped_files(bare_fs, build_opt):
    config_file = bare_fs / build_opt.config
    config_file.write_text('[tool.mccole]\nskips = ["*.text", "extras/**", "uv.lock"]\n')
    (bare_fs / build_opt.src / "alpha.text").write_text("something")
    (bare_fs / build_opt.src / "uv.lock").write_text("version = 1")
    (bare_fs / build_opt.src / "extras").mkdir()
    (bare_fs / build_opt.src / "extras" / "test.md").write_text("# test")

    build(build_opt)

    assert len(list((bare_fs / build_opt.dst).iterdir())) == 0


def test_build_boilerplate_files_correctly_renamed(bare_fs, build_opt):
    fixtures = (
        ("CODE_OF_CONDUCT.md", "Code of Conduct", "conduct"),
        ("CONTRIBUTING.md", "Contributing", "contrib"),
        ("LICENSE.md", "License", "license"),
        ("README.md", "Project", ""),
    )
    for filename, content, _ in fixtures:
        x = bare_fs / build_opt.src / filename
        x.write_text(f"# {content}\n")

    build(build_opt)

    for filename, content, output in fixtures:
        expected = bare_fs / build_opt.dst / output / "index.html"
        assert expected.is_file()
        assert content in expected.read_text()


def test_build_boilerplate_links_correctly_adjusted(bare_fs, build_opt):
    lines = (
        "# Title",
        '<section id="text" markdown="1">',
        "[conduct](./CODE_OF_CONDUCT.md)",
        "[contributing](./CONTRIBUTING.md)",
        "[license](./LICENSE.md)",
        "[home page](./README.md)",
        "</section>",
    )
    (bare_fs / build_opt.src / "test.md").write_text("\n".join(lines))

    build(build_opt)

    expected = bare_fs / build_opt.dst / "test.html"
    assert expected.is_file()
    doc = BeautifulSoup(expected.read_text(), "html.parser")
    section = doc.select("section[id='text']")[0]
    urls = {node["href"] for node in section.select("a")}
    assert urls == {"./conduct/", "./contrib/", "./license/", "./"}


def test_build_bibliography_links_correctly_adjusted(bare_fs, build_opt):
    (bare_fs / build_opt.src / "test.md").write_text("# Title\n[](b:first)\n")
    build(build_opt)
    expected = bare_fs / build_opt.dst / "test.html"
    assert expected.is_file()
    assert 'href="./bibliography/#first"' in expected.read_text()


def test_build_glossary_links_correctly_adjusted(bare_fs, build_opt):
    (bare_fs / build_opt.src / "test.md").write_text("# Title\n[term](g:key)\n")
    build(build_opt)
    expected = bare_fs / build_opt.dst / "test.html"
    assert expected.is_file()
    assert 'href="./glossary/#key"' in expected.read_text()


def test_build_glossary_keys_values_loaded(bare_fs, build_opt, glossary_path):
    glossary = _load_glossary([glossary_path])
    assert glossary == {"first": "first term", "second": "second term"}


def test_build_defined_terms_added_to_page(bare_fs, build_opt, glossary_path):
    lines = [
        "# Title",
        '<p id="terms"></p>',
        "[one](g:first) [two](g:second)"
    ]
    (bare_fs / build_opt.src / "test.md").write_text("\n".join(lines))
    build(build_opt)
    content = (bare_fs / build_opt.dst / "test.html").read_text()
    doc = BeautifulSoup(content, "html.parser")
    terms = doc.select("p#terms")[0]
    refs = {node["href"] for node in terms.select("a[href]")}
    assert refs == {"./glossary/#first", "./glossary/#second"}


def test_build_defined_terms_paragraph_removed(bare_fs, build_opt):
    lines = [
        "# Title",
        '<p id="terms"></p>',
        "body"
    ]
    (bare_fs / build_opt.src / "test.md").write_text("\n".join(lines))
    build(build_opt)
    expected = bare_fs / build_opt.dst / "test.html"
    assert expected.is_file()
    doc = BeautifulSoup(expected.read_text(), "html.parser")
    assert not doc.select("p#terms")


def test_build_backtick_code_block_class_applied_to_enclosing_pre(bare_fs, build_opt):
    (bare_fs / build_opt.src / "test.md").write_text("# Title\n```py\nx = 1\n```\n")
    build(build_opt)
    expected = bare_fs / build_opt.dst / "test.html"
    assert expected.is_file()
    doc = BeautifulSoup(expected.read_text(), "html.parser")
    for tag in ["pre", "code"]:
        nodes = doc.find_all(tag)
        assert len(nodes) == 1
        assert nodes[0]["class"] == ["language-py"]


def test_build_non_markdown_files_copied(bare_fs, build_opt):
    (bare_fs / build_opt.src / "in_root.txt").write_text("root text")
    (bare_fs / build_opt.src / "subdir").mkdir()
    (bare_fs / build_opt.src / "subdir" / "in_subdir.txt").write_text("subdir text")
    build(build_opt)
    in_root = bare_fs / build_opt.dst / "in_root.txt"
    assert in_root.is_file()
    assert in_root.read_text() == "root text"
    in_subdir = bare_fs / build_opt.dst / "subdir" / "in_subdir.txt"
    assert in_subdir.is_file()
    assert in_subdir.read_text() == "subdir text"


def test_build_warn_unknown_markdown_links(bare_fs, build_opt, capsys):
    (bare_fs / build_opt.src / "test.md").write_text("# Title\n[text](link.md)\n")
    build(build_opt)
    captured = capsys.readouterr()
    assert "unknown Markdown link" in captured.err


def test_build_warn_missing_h1(bare_fs, build_opt, capsys):
    (bare_fs / build_opt.src / "test.md").write_text("text\n")
    build(build_opt)
    captured = capsys.readouterr()
    assert "lacks H1 heading" in captured.err


def test_build_warn_missing_title(bare_fs, build_opt, capsys):
    template_path = bare_fs / build_opt.templates / "page.html"
    template = template_path.read_text()
    template = template.replace("<title></title>", "")
    template_path.write_text(template)

    (bare_fs / build_opt.src / "test.md").write_text("text\n")
    build(build_opt)
    captured = capsys.readouterr()
    assert "does not have <title> element" in captured.err


def test_build_warn_badly_formatted_config_file(bare_fs, build_opt, capsys):
    config_file = bare_fs / "pyproject.toml"
    config_file.write_text('[tool.missing]\nskips = ["extras", "uv.lock"]\n')

    build(build_opt)
    captured = capsys.readouterr()
    assert "does not have 'tool.mccole'" in captured.err


def test_build_warn_overlap_renames_and_skips(bare_fs, build_opt, capsys):
    config_file = bare_fs / "pyproject.toml"
    config_file.write_text('[tool.mccole]\nskips = ["LICENSE.md"]\n')
    (bare_fs / build_opt.src / "LICENSE.md").write_text("# License")

    build(build_opt)
    captured = capsys.readouterr()
    assert "overlap between skips and renames" in captured.err


def test_build_warn_multiple_term_paragraphs_in_doc(bare_fs, build_opt, capsys):
    lines = [
        "# Terms",
        '<p id="terms"></p>',
        '<p id="terms"></p>',
    ]
    (bare_fs / build_opt.src / "test.md").write_text("\n".join(lines))

    build(build_opt)
    captured = capsys.readouterr()
    assert "terms paragraph appears multiple times" in captured.err


def test_build_warn_multiple_glossary_files_found(bare_fs, build_opt, capsys):
    (bare_fs / build_opt.src / "glossary").mkdir()
    (bare_fs / build_opt.src / "glossary" / "index.md").write_text("# First")
    (bare_fs / build_opt.src / "subdir").mkdir()
    (bare_fs / build_opt.src / "subdir" / "glossary").mkdir()
    (bare_fs / build_opt.src / "subdir" / "glossary" / "index.md").write_text("# Second")
    build(build_opt)
    captured = capsys.readouterr()
    assert "multiple glossary files" in captured.err

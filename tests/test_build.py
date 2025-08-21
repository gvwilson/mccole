"""Test that sites build."""

import argparse

import pytest

from mccole.build import main as build, construct_parser, _load_glossary
from .conftest import README, make_fs, read_doc


TABLE_MD = """\
# Title

<div markdown="1" data-table-id="t:tbl" data-table-caption="Table Title">
| left | right |
| ---- | ----- |
| 1    | 2     |
| 3    | 4     |
</div>
"""


def test_construct_parser_with_default_values():
    parser = argparse.ArgumentParser()
    construct_parser(parser)
    opt = parser.parse_args([])
    assert all(hasattr(opt, key) for key in ["config", "dst", "src", "templates"])


def test_with_minimal_files(bare_fs, build_opt, minimal_dst_top_level):
    build(build_opt)
    dst = bare_fs / build_opt.dst
    assert dst.is_dir()
    assert set(dst.iterdir()) == minimal_dst_top_level


def test_with_single_plain_markdown_file_creates_output_file(bare_fs, build_opt):
    make_fs({bare_fs / build_opt.src / "test.md": "# Title\nbody"})
    build(build_opt)

    expected = bare_fs / build_opt.dst / "test.html"
    assert expected.is_file()

    doc = read_doc(expected)
    assert doc.title.string == "Title"
    paragraphs = doc.find_all("p")
    assert len(paragraphs) == 1 and paragraphs[0].string == "body"


def test_does_not_copy_dot_files(bare_fs, build_opt, minimal_dst_top_level):
    make_fs(
        {
            bare_fs / build_opt.src / ".gitignore": "content",
        }
    )
    build(build_opt)
    assert set((bare_fs / build_opt.dst).iterdir()) == minimal_dst_top_level


def test_does_not_copy_dot_dirs(bare_fs, build_opt, minimal_dst_top_level):
    (bare_fs / build_opt.src / ".settings").mkdir()
    build(build_opt)
    assert set((bare_fs / build_opt.dst).iterdir()) == minimal_dst_top_level


def test_does_not_copy_symlinks(bare_fs, build_opt, minimal_dst_top_level):
    (bare_fs / build_opt.src / "link.lnk").symlink_to("/tmp")
    build(build_opt)
    assert set((bare_fs / build_opt.dst).iterdir()) == minimal_dst_top_level


def test_does_not_copy_destination_files(bare_fs, build_opt, minimal_dst_top_level):
    dst_path = bare_fs / build_opt.dst / "existing.html"
    make_fs(
        {
            dst_path: "<html></html>",
        }
    )
    build(build_opt)
    expected = minimal_dst_top_level | {dst_path}
    assert set((bare_fs / build_opt.dst).iterdir()) == expected


def test_does_not_copy_explicitly_skipped_files(
    bare_fs, build_opt, minimal_dst_top_level
):
    config_file = bare_fs / build_opt.config
    make_fs(
        {
            config_file: '[tool.mccole]\nskips = ["*.text", "extras/**", "uv.lock"]\n',
            bare_fs / build_opt.src / "alpha.text": "something",
            bare_fs / build_opt.src / "uv.lock": "version = 1",
            bare_fs / build_opt.src / "extras" / "test.md": "# test",
        }
    )
    build(build_opt)
    assert set((bare_fs / build_opt.dst).iterdir()) == minimal_dst_top_level


def test_footer_title_filled_in_correctly(bare_fs, build_opt, readme_dst_file):
    build(build_opt)
    doc = read_doc(readme_dst_file)
    footer = doc.select_one("footer")
    assert footer is not None
    links = {node["href"]: node.get_text() for node in footer.select("a[href]")}
    assert "./" in links
    assert links["./"] == "Tutorial"
    assert "./#acknowledgments" in links


def test_boilerplate_files_correctly_renamed(bare_fs, build_opt):
    fixtures = (
        ("CODE_OF_CONDUCT.md", "Code of Conduct", "conduct"),
        ("CONTRIBUTING.md", "Contributing", "contrib"),
        ("LICENSE.md", "License", "license"),
    )
    for filename, content, _ in fixtures:
        x = bare_fs / build_opt.src / filename
        x.write_text(f"# {content}\n")

    build(build_opt)

    for filename, content, output in fixtures:
        expected = bare_fs / build_opt.dst / output / "index.html"
        assert expected.is_file()
        assert content in expected.read_text()


def test_boilerplate_links_correctly_adjusted(bare_fs, build_opt):
    text = """\
# Title
<section id="text" markdown="1">
[conduct](./CODE_OF_CONDUCT.md)
[contributing](./CONTRIBUTING.md)
[license](./LICENSE.md)
[home page](./README.md)
</section>
"""
    make_fs({bare_fs / build_opt.src / "test.md": text})
    build(build_opt)

    expected = bare_fs / build_opt.dst / "test.html"
    assert expected.is_file()
    doc = read_doc(expected)
    section = doc.select("section[id='text']")[0]
    urls = {node["href"] for node in section.select("a")}
    assert urls == {"./conduct/", "./contrib/", "./license/", "./"}


def test_bibliography_links_correctly_adjusted(bare_fs, build_opt):
    make_fs(
        {
            bare_fs / build_opt.src / "test.md": "# Title\n[](b:first)\n",
        }
    )
    build(build_opt)
    expected = bare_fs / build_opt.dst / "test.html"
    assert expected.is_file()
    assert 'href="./bibliography/#first"' in expected.read_text()


def test_glossary_links_correctly_adjusted(bare_fs, build_opt):
    make_fs(
        {
            bare_fs / build_opt.src / "test.md": "# Title\n[term](g:key)\n",
        }
    )
    build(build_opt)
    expected = bare_fs / build_opt.dst / "test.html"
    assert expected.is_file()
    assert 'href="./glossary/#key"' in expected.read_text()


def test_glossary_keys_values_loaded(bare_fs, build_opt, glossary_src_file):
    glossary = _load_glossary([glossary_src_file])
    assert glossary == {"first": "first term", "second": "second term"}


def test_defined_terms_added_to_page(bare_fs, build_opt, glossary_dst_file):
    text = """\
# Title
<p id="terms"></p>
[one](g:first) [two](g:second)
"""
    make_fs(
        {
            bare_fs / build_opt.src / "test.md": text,
        }
    )
    build(build_opt)
    doc = read_doc(bare_fs / build_opt.dst / "test.html")
    terms = doc.select("p#terms")[0]
    refs = {node["href"] for node in terms.select("a[href]")}
    assert refs == {"./glossary/#first", "./glossary/#second"}


def test_defined_terms_paragraph_removed(bare_fs, build_opt):
    text = """\
# Title
<p id="terms"></p>
body
"""
    make_fs(
        {
            bare_fs / build_opt.src / "test.md": text,
        }
    )
    build(build_opt)
    expected = bare_fs / build_opt.dst / "test.html"
    assert expected.is_file()
    doc = read_doc(expected)
    assert not doc.select("p#terms")


def test_backtick_code_block_class_applied_to_enclosing_pre(bare_fs, build_opt):
    text = """\
# Title
```py
x = 1
```
"""
    make_fs(
        {
            bare_fs / build_opt.src / "test.md": text,
        }
    )
    build(build_opt)
    expected = bare_fs / build_opt.dst / "test.html"
    assert expected.is_file()
    doc = read_doc(expected)
    for tag in ["pre", "code"]:
        nodes = doc.find_all(tag)
        assert len(nodes) == 1
        assert nodes[0]["class"] == ["language-py"]


def test_non_markdown_files_copied(bare_fs, build_opt):
    make_fs(
        {
            bare_fs / build_opt.src / "in_root.txt": "root text",
            bare_fs / build_opt.src / "subdir" / "in_subdir.txt": "subdir text",
        }
    )
    build(build_opt)

    in_root = bare_fs / build_opt.dst / "in_root.txt"
    assert in_root.is_file()
    assert in_root.read_text() == "root text"

    in_subdir = bare_fs / build_opt.dst / "subdir" / "in_subdir.txt"
    assert in_subdir.is_file()
    assert in_subdir.read_text() == "subdir text"


def test_append_provided_links_file(bare_fs, build_opt):
    text = """\
# Title
[link][url]
"""
    links_path = bare_fs / build_opt.src / "links.txt"
    test_url = "http://some.url/"
    make_fs(
        {
            bare_fs / build_opt.src / "test.md": text,
            links_path: f"[url]: {test_url}",
        }
    )
    build_opt.links = links_path
    build(build_opt)

    doc = read_doc(bare_fs / build_opt.dst / "test.html")
    links = doc.main.select("a")
    assert len(links) == 1
    assert links[0]["href"] == test_url


def test_labels_figures(bare_fs, build_opt):
    text = """
# Title
<figure id='f:first'><figcaption>caption</figcaption></figure>
"""
    make_fs(
        {
            bare_fs / build_opt.src / "test.md": text,
        }
    )
    build(build_opt)

    doc = read_doc(bare_fs / build_opt.dst / "test.html")
    captions = doc.select("figcaption")
    assert len(captions) == 1
    assert captions[0].string == "Figure 1: caption"


def test_cross_references_figures(bare_fs, build_opt):
    text = """\
# Title
<figure id='f:first'><figcaption>caption</figcaption></figure>
text [](#f:first)
"""
    make_fs(
        {
            bare_fs / build_opt.src / "test.md": text,
        }
    )
    build(build_opt)

    doc = read_doc(bare_fs / build_opt.dst / "test.html")
    links = [node for node in doc.select("a[href]") if node["href"].startswith("#f:")]
    assert len(links) == 1
    assert links[0].string == "Figure 1"


def test_create_table_correctly(bare_fs, build_opt):
    make_fs(
        {
            bare_fs / build_opt.src / "test.md": TABLE_MD,
        }
    )
    build(build_opt)

    doc = read_doc(bare_fs / build_opt.dst / "test.html")
    nodes = {}
    for selector in ["table", "thead", "tbody", "caption"]:
        found = doc.select(selector)
        assert len(found) == 1
        nodes[selector] = found[0]

    assert nodes["table"]["id"] == "t:tbl"
    assert nodes["caption"].string == "Table Title"

    assert len(nodes["thead"].select("tr")) == 1
    assert len(nodes["thead"].select("th")) == 2
    assert len(nodes["thead"].select("td")) == 0
    assert set(n.string for n in nodes["thead"].select("th")) == {"left", "right"}

    assert len(nodes["tbody"].select("tr")) == 2
    assert len(nodes["tbody"].select("th")) == 0
    assert len(nodes["tbody"].select("td")) == 4
    assert set(n.string for n in nodes["tbody"].select("td")) == {"1", "2", "3", "4"}


def test_table_cross_reference(bare_fs, build_opt):
    text = f"""\
{TABLE_MD}
text [](#t:tbl)
"""
    make_fs(
        {
            bare_fs / build_opt.src / "test.md": text,
        }
    )
    build(build_opt)
    doc = read_doc(bare_fs / build_opt.dst / "test.html")
    links = [node for node in doc.select("a[href]") if node["href"].startswith("#t:")]
    assert len(links) == 1
    assert links[0].string == "Table 1"


def test_fail_badly_formatted_internal_readme_link(bare_fs, build_opt):
    readme = build_opt.src / "README.md"
    content = readme.read_text()
    content = content.replace('(./', '(../')
    readme.write_text(content)
    with pytest.raises(AssertionError):
        build(build_opt)


def test_warn_unknown_markdown_links(bare_fs, build_opt, capsys):
    make_fs(
        {
            bare_fs / build_opt.src / "test.md": "# Title\n[text](link.md)\n",
        }
    )
    build(build_opt)
    captured = capsys.readouterr()
    assert "unknown Markdown link" in captured.err


def test_warn_missing_h1(bare_fs, build_opt, capsys):
    make_fs({bare_fs / build_opt.src / "test.md": "text\n"})
    build(build_opt)
    captured = capsys.readouterr()
    assert "lacks H1 heading" in captured.err


def test_warn_missing_title(bare_fs, build_opt, capsys):
    template_path = bare_fs / build_opt.templates / "page.html"
    template = template_path.read_text()
    template = template.replace("<title></title>", "")
    template_path.write_text(template)

    make_fs(
        {
            bare_fs / build_opt.src / "test.md": "text\n",
        }
    )
    build(build_opt)
    captured = capsys.readouterr()
    assert "does not have <title> element" in captured.err


def test_warn_badly_formatted_config_file(bare_fs, build_opt, capsys):
    config_file = bare_fs / "pyproject.toml"
    make_fs({config_file: '[tool.missing]\nskips = ["extras", "uv.lock"]\n'})
    build(build_opt)
    captured = capsys.readouterr()
    assert "does not have 'tool.mccole'" in captured.err


def test_warn_overlap_renames_and_skips(bare_fs, build_opt, capsys):
    config_file = bare_fs / "pyproject.toml"
    make_fs(
        {
            config_file: '[tool.mccole]\nskips = ["LICENSE.md"]\n',
            bare_fs / build_opt.src / "LICENSE.md": "# License",
        }
    )
    build(build_opt)
    captured = capsys.readouterr()
    assert "overlap between skips and renames" in captured.err


def test_warn_multiple_term_paragraphs_in_doc(bare_fs, build_opt, capsys):
    text = """\
# Terms
<p id="terms"></p>
<p id="terms"></p>
"""
    make_fs(
        {
            bare_fs / build_opt.src / "test.md": text,
        }
    )
    build(build_opt)
    captured = capsys.readouterr()
    assert "terms paragraph appears multiple times" in captured.err


def test_warn_no_glossary_file_found(bare_fs, build_opt, glossary_src_file, capsys):
    glossary_src_file.unlink()
    glossary_src_file.parent.rmdir()
    build(build_opt)
    captured = capsys.readouterr()
    assert "no glossary found" in captured.err


def test_warn_multiple_glossary_files_found(bare_fs, build_opt, capsys):
    make_fs(
        {
            bare_fs / build_opt.src / "subdir" / "glossary" / "index.md": "# Second",
        }
    )
    build(build_opt)
    captured = capsys.readouterr()
    assert "multiple glossary files" in captured.err


def test_warn_figure_missing_id(bare_fs, build_opt, capsys):
    text = """\
# Title
<figure><figcaption>caption</figcaption></figure>
"""
    make_fs(
        {
            bare_fs / build_opt.src / "test.md": text,
        }
    )
    build(build_opt)
    captured = capsys.readouterr()
    assert "has no ID" in captured.err


def test_warn_figure_id_wrong_prefix(bare_fs, build_opt, capsys):
    text = """\
# Title
<figure id='something'><figcaption>caption</figcaption></figure>
"""
    make_fs(
        {
            bare_fs / build_opt.src / "test.md": text,
        }
    )
    build(build_opt)
    captured = capsys.readouterr()
    assert "does not start with" in captured.err


def test_warn_figure_multiple_captions(bare_fs, build_opt, capsys):
    text = """
# Title
<figure id='f:fig'><figcaption>caption</figcaption><figcaption>another</figcaption></figure>
"""
    make_fs(
        {
            bare_fs / build_opt.src / "test.md": text,
        }
    )
    build(build_opt)
    captured = capsys.readouterr()
    assert "has missing/too many captions" in captured.err


def test_warn_figure_missing_caption(bare_fs, build_opt, capsys):
    text = """\
# Title
<figure id='f:fig'></figure>
"""
    make_fs(
        {
            bare_fs / build_opt.src / "test.md": text,
        }
    )
    build(build_opt)
    captured = capsys.readouterr()
    assert "has missing/too many captions" in captured.err


def test_warn_figure_reference_cannot_be_resolved(bare_fs, build_opt, capsys):
    text = """\
# Title
<figure id='f:fig'><figcaption>caption</figcaption></figure>
text [](#f:missing)
"""
    make_fs(
        {
            bare_fs / build_opt.src / "test.md": text,
        }
    )
    build(build_opt)
    captured = capsys.readouterr()
    assert "cannot resolve figure reference" in captured.err


def test_warn_table_id_wrong_prefix(bare_fs, build_opt, capsys):
    text = TABLE_MD.replace("t:tbl", "something")
    make_fs(
        {
            bare_fs / build_opt.src / "test.md": text,
        }
    )
    build(build_opt)
    captured = capsys.readouterr()
    assert "does not start with 't:'" in captured.err


def test_warn_table_missing_caption(bare_fs, build_opt, capsys):
    text = TABLE_MD.replace("data-table-caption", "data-something")
    make_fs(
        {
            bare_fs / build_opt.src / "test.md": text,
        }
    )
    build(build_opt)
    captured = capsys.readouterr()
    assert "does not have data-table-caption" in captured.err


def test_warn_table_no_table_element(bare_fs, build_opt, capsys):
    text = """\
# Title

<div markdown="1" data-table-id="t:tbl" data-table-caption="Table Title">
<p>Not a table</p>
</div>
"""
    make_fs(
        {
            bare_fs / build_opt.src / "test.md": text,
        }
    )
    build(build_opt)
    captured = capsys.readouterr()
    assert "does not contain table" in captured.err


def test_warn_table_reference_cannot_be_resolved(bare_fs, build_opt, capsys):
    text = f"""\
{TABLE_MD}
text [](#t:missing)
"""
    make_fs(
        {
            bare_fs / build_opt.src / "test.md": text,
        }
    )
    build(build_opt)
    captured = capsys.readouterr()
    assert "cannot resolve table reference" in captured.err

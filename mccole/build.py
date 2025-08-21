"""Build HTML site from source files."""

import argparse
from pathlib import Path
import re
import sys

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
from markdown import markdown
import tomli


BOILERPLATE = {
    "README.md": Path(""),
    "CODE_OF_CONDUCT.md": Path("conduct"),
    "CONTRIBUTING.md": Path("contrib"),
    "LICENSE.md": Path("license"),
}
GLOSSARY_MD = re.compile(r'^<span\s+id="(.+?)"\s*>(.+?)</span>', re.MULTILINE)
MARKDOWN_EXTENSIONS = ["attr_list", "def_list", "fenced_code", "md_in_html", "tables"]


def main(opt):
    """Main driver."""
    opt.settings = _load_config(opt.config)
    opt._links = opt.links.read_text() if opt.links else None
    files = _find_files(opt)
    markdown, others = _separate_files(files)
    opt._glossary = _load_glossary(markdown)
    opt.dst.mkdir(parents=True, exist_ok=True)

    env = Environment(loader=FileSystemLoader(opt.templates))
    context = _get_context_from_readme(opt)
    _handle_markdown(opt, env, context, markdown)
    _handle_others(opt, others)


def construct_parser(parser):
    """Parse command-line arguments."""
    parser.add_argument(
        "--config", default=Path("pyproject.toml"), help="configuration file"
    )
    parser.add_argument(
        "--dst", type=Path, default=Path("docs"), help="output directory"
    )
    parser.add_argument("--links", type=Path, default=None, help="links file")
    parser.add_argument("--src", type=Path, default=Path("."), help="source directory")
    parser.add_argument(
        "--templates", type=Path, default="templates", help="templates directory"
    )


def _create_figure_numbers(dest, doc):
    """Modify figures, building key-to-number lookup."""
    seen = {}
    for i, figure in enumerate(doc.select("figure")):
        fig_num = i + 1
        if "id" not in figure.attrs:
            _warn(f"figure {fig_num} in {dest} has no ID")
            continue
        if not figure["id"].startswith("f:"):
            _warn(f"figure {fig_num} in {dest} does not start with 'f:'")
            continue
        captions = figure.select("figcaption")
        if len(captions) != 1:
            _warn(f"figure {fig_num} in {dest} has missing/too many captions")
            continue
        caption = captions[0]
        seen[figure["id"]] = fig_num
        caption.insert(0, f"Figure {fig_num}: ")
    return seen


def _create_table_numbers(dest, doc):
    """Modify tables, building key-to-number lookup."""
    seen = {}
    for i, div in enumerate(doc.select("div[data-table-id]")):
        tbl_num = i + 1
        if not div["data-table-id"].startswith("t:"):
            _warn(f"table {tbl_num} in {dest} does not start with 't:'")
            continue

        if "data-table-caption" not in div.attrs:
            _warn(f"table {tbl_num} in {dest} does not have data-table-caption")
            continue
        caption = div["data-table-caption"]

        tables = div.select("table")
        if len(tables) != 1:
            _warn(f"table {tbl_num} in {dest} does not contain table")
            continue

        table = tables[0]
        table["id"] = div["data-table-id"]
        caption_node = doc.new_tag("caption")
        caption_node.string = caption
        table.append(caption_node)

        seen[div["data-table-id"]] = tbl_num

    return seen


def _do_bibliography_links(opt, dest, doc):
    """Handle 'b:' bibliography links."""
    for node in doc.select("a[href]"):
        if not node["href"].startswith("b:"):
            continue
        assert node["href"].count(":") == 1
        key = node["href"].split(":")[1]
        node.string = key
        node["href"] = _make_root_prefix(opt, dest) + f"bibliography/#{key}"


def _do_figures(opt, dest, doc):
    """Insert figure numbers."""
    seen = _create_figure_numbers(dest, doc)
    _update_cross_references(dest, doc, seen, "figure", "#f:", "Figure")


def _do_glossary_links(opt, dest, doc):
    """Handle 'g:' glossary links."""
    for node in doc.select("a[href]"):
        if not node["href"].startswith("g:"):
            continue
        assert node["href"].count(":") == 1
        key = node["href"].split(":")[1]
        node["href"] = _make_root_prefix(opt, dest) + f"glossary/#{key}"


def _do_glossary_terms(opt, dest, doc):
    """Fill in <p id="terms"></p> if present and terms defined."""
    targets = doc.select("p#terms")
    if len(targets) == 0:
        return
    if len(targets) > 1:
        _warn(f"terms paragraph appears multiple times in {dest}")
        return
    target = targets[0]

    found = {
        node["href"].split("#")[-1]: node["href"]
        for node in doc.select("a[href]")
        if "/glossary/#" in node["href"]
    }
    if not found:
        target.decompose()
        return

    entries = [(key, opt._glossary.get(key, "UNDEFINED")) for key in found.keys()]
    entries.sort(key=lambda item: item[1])
    target.append("Terms defined: ")
    for i, (key, term) in enumerate(entries):
        tag = doc.new_tag("a", href=found[key])
        tag.string = term
        if i > 0:
            target.append(", ")
        target.append(tag)


def _do_markdown_links(opt, dest, doc):
    """Handle ./SOMETHING.md links."""
    for node in doc.select("a[href]"):
        if not node["href"].endswith(".md"):
            continue
        target = str(Path(node["href"]).name)
        if target not in BOILERPLATE:
            _warn(f"unknown Markdown link {node['href']} for {dest}")
            continue
        node["href"] = f"@/" if target == "README.md" else f"@/{BOILERPLATE[target]}/"


def _do_pre_code_classes(opt, dest, doc):
    """Add language classes to <pre> elements."""
    for node in doc.select("pre>code"):
        cls = node.get("class", [])
        node.parent["class"] = node.parent.get("class", []) + cls


def _do_root_links(opt, dest, doc):
    """Handle '@/' links."""
    prefix = _make_root_prefix(opt, dest)
    targets = (
        ("a[href]", "href"),
        ("img[src]", "src"),
        ("link[href]", "href"),
        ("script[src]", "src"),
    )
    for selector, attr in targets:
        for node in doc.select(selector):
            if node[attr].startswith("@/"):
                node[attr] = node[attr].replace("@/", prefix)


def _do_tables(opt, dest, doc):
    """Insert figure numbers."""
    seen = _create_table_numbers(dest, doc)
    _update_cross_references(dest, doc, seen, "table", "#t:", "Table")


def _do_title(opt, dest, doc):
    """Make sure title element is filled in."""
    if doc.title is None:
        _warn(f"{dest} does not have <title> element")
        return
    try:
        doc.title.string = doc.h1.get_text()
    except Exception:
        _warn(f"{dest} lacks H1 heading")


def _find_files(opt):
    """Collect all interesting files."""
    return [path for path in opt.src.glob("**/*.*") if _is_interesting_file(opt, path)]


def _get_context_from_readme(opt):
    """Get values for template expansion from README.md"""

    def fix_url(url):
        assert url.startswith("./"), f"bad README internal url {url}"
        return url.replace("./", "@/", 1)

    md = (opt.src / "README.md").read_text()
    html = markdown(md, extensions=MARKDOWN_EXTENSIONS)
    doc = BeautifulSoup(html, "html.parser")
    title = doc.select_one("h1").decode_contents()
    lessons = {
        fix_url(node["href"]): node.decode_contents()
        for node in doc.select("div#lessons")[0].select("a[href]")
    }
    appendices = {
        fix_url(node["href"]): node.decode_contents()
        for node in doc.select("div#appendices")[0].select("a[href]")
    }
    return {
        "title": title,
        "lessons": lessons,
        "appendices": appendices,
    }


def _handle_markdown(opt, env, context, files):
    """Handle Markdown files."""
    for source in files:
        dest = _make_output_path(opt, source)
        html = _render_markdown(opt, env, context, source, dest)
        dest.write_text(html)


def _handle_others(opt, files):
    """Handle copy-only files."""
    for source in files:
        dest = _make_output_path(opt, source)
        content = source.read_bytes()
        dest.write_bytes(content)


def _is_interesting_file(opt, path):
    """Is this file worth copying over?"""
    relative = path.relative_to(opt.src)
    if not path.is_file():
        return False
    if str(relative).startswith("."):
        return False
    if path.samefile(opt.config):
        return False
    if path.is_relative_to(opt.dst):
        return False
    if path.is_relative_to(opt.templates):
        return False

    skips = opt.settings["skips"]
    for s in skips:
        if s.endswith("/**") and relative.is_relative_to(s.replace("/**", "")):
            return False
        if path.match(s):
            return False

    return True


def _load_config(filepath):
    """Read configuration data."""
    config = tomli.loads(filepath.read_text())

    if ("tool" not in config) or ("mccole" not in config["tool"]):
        _warn(f"configuration file {filepath} does not have 'tool.mccole'")
        return {"skips": set()}

    config = config["tool"]["mccole"]
    config["skips"] = set(config["skips"]) if "skips" in config else set()

    overlap = set(BOILERPLATE.keys()) & config["skips"]
    if overlap:
        _warn(
            f"overlap between skips and renames in config {filepath}: {', '.join(sorted(overlap))}"
        )

    return config


def _load_glossary(markdown_filenames):
    """Get key:term pairs from glossary."""
    paths = [p for p in markdown_filenames if "glossary/index.md" in str(p)]
    if len(paths) == 0:
        _warn(f"no glossary found")
        return {}
    elif len(paths) > 1:
        _warn(f"multiple glossary files")
        return {}
    content = paths[0].read_text()
    return {m[0]: m[1] for m in GLOSSARY_MD.findall(content)}


def _make_output_path(opt, source):
    """Build output path."""
    source_str = str(source.name)
    temp = BOILERPLATE[source_str] / "index.md" if source_str in BOILERPLATE else source
    temp = temp.with_suffix("").with_suffix(".html") if temp.suffix == ".md" else temp
    temp = opt.src / temp
    result = opt.dst / temp.relative_to(opt.src)
    result.parent.mkdir(parents=True, exist_ok=True)
    return result


def _make_root_prefix(opt, path):
    """Create prefix to root for path."""
    relative = path.relative_to(opt.dst)
    depth = len(relative.parents) - 1
    assert depth >= 0
    return "./" if (depth == 0) else "../" * depth


def _render_markdown(opt, env, context, source, dest):
    """Convert Markdown to HTML."""
    content = source.read_text()
    if opt._links:
        content += "\n" + opt._links
    template_name = "slides.html" if source.name == "slides.md" else "page.html"
    template = env.get_template(template_name)
    raw_html = markdown(content, extensions=MARKDOWN_EXTENSIONS)
    rendered_html = template.render(content=raw_html, **context)

    doc = BeautifulSoup(rendered_html, "html.parser")
    for func in [
        _do_bibliography_links,
        _do_figures,
        _do_glossary_links,
        _do_glossary_terms,
        _do_markdown_links,
        _do_pre_code_classes,
        _do_root_links,
        _do_tables,
        _do_title,
    ]:
        func(opt, dest, doc)

    return str(doc)


def _separate_files(files):
    """Divide files into categories."""
    markdown = [path for path in files if path.suffix == ".md"]
    others = [path for path in files if path.suffix != ".md"]
    return markdown, others


def _update_cross_references(dest, doc, seen, kind, prefix, caption):
    """Modify cross-references to figures."""
    for ref in doc.select("a[href]"):
        if not ref["href"].startswith(prefix):
            continue
        key = ref["href"][1:]
        if key not in seen:
            _warn(f"cannot resolve {kind} reference {ref['href']} in {dest}")
            continue
        ref.string = f"{caption} {seen[key]}"


def _warn(msg):
    """Print warning."""
    print(msg, file=sys.stderr)

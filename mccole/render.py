"""Convert Markdown to HTML."""

import argparse
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
from markdown import markdown
from pathlib import Path

from .util import find_files, get_inclusion, load_config, write_file


MARKDOWN_EXTENSIONS = ["attr_list", "def_list", "fenced_code", "md_in_html", "tables"]


def render(opt):
    """Main driver."""
    config = load_config(opt.config)
    skips = config["skips"] | {opt.out}
    env = Environment(loader=FileSystemLoader(opt.templates))

    files = find_files(opt, skips)
    files = {filepath: {"content": content} for filepath, content in files.items()}

    sections = {
        filepath: info
        for filepath, info in files.items()
        if filepath.suffix == ".md"
    }
    for filepath, info in sections.items():
        info["doc"] = render_markdown(env, opt, filepath, info["content"])

    for filepath, info in files.items():
        result = str(info["doc"]) if filepath.suffix == ".md" else info["content"]
        output_path = make_output_path(opt.out, config["renames"], filepath)
        write_file(output_path, result)


def choose_template(env, source_path):
    """Select a template."""
    if source_path.name == "slides.md":
        return env.get_template("slides.html")
    return env.get_template("page.html")


def do_bibliography_links(doc, source_path):
    """Turn 'b:key' links into bibliography references."""
    for node in doc.select("a[href]"):
        if node["href"].startswith("b:"):
            node["href"] = f"@root/bibliography.html#{node['href'][2:]}"


def do_glossary_links(doc, source_path):
    """Turn 'g:key' links into glossary references."""
    for node in doc.select("a[href]"):
        if node["href"].startswith("g:"):
            node["href"] = f"@root/glossary.html#{node['href'][2:]}"


def do_inclusions_classes(doc, source_path):
    """Adjust classes of file inclusions."""
    for node in doc.select("code[file]"):
        inc_text = node["file"]
        if ":" in inc_text:
            inc_text = inc_text.split(":")[0]
        suffix = inc_text.split(".")[-1]
        for n in (node, node.parent):
            n["class"] = n.get("class", []) + [f"language-{suffix}"]


def do_markdown_links(doc, source_path):
    """Fix .md links in HTML."""
    for node in doc.select("a[href]"):
        if node["href"].endswith(".md"):
            node["href"] = node["href"].replace(".md", ".html").lower()


def do_tables(doc, source_path):
    """Eliminate duplicate table tags created by Markdown tables inside HTML tables."""
    for node in doc.select("table"):
        parent = node.parent
        if parent.name == "table":
            caption = parent.caption
            node.append(caption)
            parent.replace_with(node)


def do_title(doc, source_path):
    """Make sure title element is filled in."""
    doc.title.string = doc.h1.get_text()


def do_root_path_prefix(doc, source_path):
    """Fix @root links in HTML."""
    depth = len(source_path.parents) - 1
    prefix = "./" if (depth == 0) else "../" * depth
    targets = (
        ("a[href]", "href"),
        ("link[href]", "href"),
        ("script[src]", "src"),
    )
    for selector, attr in targets:
        for node in doc.select(selector):
            if "@root/" in node[attr]:
                node[attr] = node[attr].replace("@root/", prefix)


def do_toc_lists(doc, source_path):
    """Fix 'chapters' and 'appendices' lists."""
    for kind in ("chapters", "appendices"):
        selector = f"ol.{kind} ol"
        for node in doc.select(selector):
            node.parent.replace_with(node)
            node["class"] = node.get("class", []) + [kind]


def find_ordering(sections):
    """Create filepath-to-label ordering."""
    doc = sections[Path("README.md")]["doc"]
    chapters = {
        key: str(i+1)
        for i, key in enumerate(find_ordering_items(doc, "ol.chapters"))
    }
    appendices = {
        key: chr(ord("A")+i)
        for i, key in enumerate(find_ordering_items(doc, "ol.appendices"))
    }
    return {**chapters, **appendices}


def find_ordering_items(doc, selector):
    """Extract ordered items' filepath keys."""
    nodes = doc.select(selector)
    assert len(nodes) == 1
    return [
        link.select("a")[0]["href"].replace("/index.html", "").split("/")[-1]
        for link in nodes[0].select("li")
    ]


def fix_cross_references(sections, xref):
    """Fix all cross-references."""


def make_output_path(output_dir, renames, source_path):
    """Build output path."""
    if source_path.name in renames:
        source_path = Path(source_path.parent, renames[source_path.name])
    source_path = Path(str(source_path).replace(".md", ".html"))
    return Path(output_dir, source_path)


def parse_args(parser):
    """Parse command-line arguments."""
    parser.add_argument("--config", type=str, default="pyproject.toml", help="optional configuration file")
    parser.add_argument("--css", type=str, help="CSS file")
    parser.add_argument("--icon", type=str, help="icon file")
    parser.add_argument("--out", type=str, default="docs", help="output directory")
    parser.add_argument("--root", type=str, default=".", help="root directory")
    parser.add_argument("--templates", type=str, default="templates", help="templates directory")


def render_markdown(env, opt, source_path, content):
    """Convert Markdown to HTML."""
    template = choose_template(env, source_path)
    html = markdown(content, extensions=MARKDOWN_EXTENSIONS)
    html = template.render(content=html, css_file=opt.css, icon_file=opt.icon)

    transformers = (
        do_bibliography_links,
        do_glossary_links,
        do_inclusions_classes,
        do_markdown_links,
        do_tables,
        do_title,
        do_toc_lists,
        do_root_path_prefix, # must be last
    )
    doc = BeautifulSoup(html, "html.parser")
    for func in transformers:
        func(doc, source_path)

    return doc


if __name__ == "__main__":
    opt = parse_args(argparse.ArgumentParser()).parse_args()
    render(opt)

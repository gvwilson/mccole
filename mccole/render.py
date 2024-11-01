"""Convert Markdown to HTML."""

import argparse
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
from markdown import markdown
from pathlib import Path

from .util import find_files, load_config, write_file


ALSO_HTML_EXT = {".css", ".js", ".py", ".sql"}
MARKDOWN_EXTENSIONS = ["attr_list", "def_list", "fenced_code", "md_in_html", "tables"]


def render(opt):
    """Main driver."""
    config = load_config(opt.config)
    skips = config["skips"] | {opt.out} | set(opt.exclude)
    files = find_files(opt, skips)
    env = Environment(loader=FileSystemLoader(opt.templates))
    for filepath, content in files.items():
        if filepath.suffix == ".md":
            render_markdown(env, opt, config["renames"], filepath, content)
        elif filepath.suffix in ALSO_HTML_EXT:
            render_markdown(env, opt, config["renames"], filepath, content, as_html=True)
            copy_file(opt.out, config["renames"], filepath, content)
        else:
            copy_file(opt.out, config["renames"], filepath, content)


def choose_template(env, source_path):
    """Select a template."""
    if source_path.name == "slides.md":
        return env.get_template("slides.html")
    return env.get_template("page.html")


def copy_file(output_dir, renames, source_path, content):
    """Copy a file verbatim."""
    output_path = make_output_path(output_dir, renames, source_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_file(output_path, content)


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


def do_interfile_links(doc, source_path):
    """Fix suffix links in HTML."""
    for node in doc.select("a[href]"):
        if node["href"].endswith(".md"):
            node["href"] = node["href"].replace(".md", ".html").lower()
        elif Path(node["href"]).suffix in ALSO_HTML_EXT:
            node["href"] = f"{node['href']}.html"


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
    parser.add_argument("--exclude", nargs="+", default=[], help="root items to exclude")
    parser.add_argument("--icon", type=str, help="icon file")
    parser.add_argument("--out", type=str, default="docs", help="output directory")
    parser.add_argument("--root", type=str, default=".", help="root directory")
    parser.add_argument("--templates", type=str, default="templates", help="templates directory")


def render_markdown(env, opt, renames, source_path, content, as_html=False):
    """Convert Markdown to HTML."""
    if as_html:
        content = f"# {source_path}\n```\n{content}```"
    template = choose_template(env, source_path)
    html = markdown(content, extensions=MARKDOWN_EXTENSIONS)
    html = template.render(content=html, css_file=opt.css, icon_file=opt.icon)

    transformers = (
        do_bibliography_links,
        do_glossary_links,
        do_interfile_links,
        do_tables,
        do_title,
        do_toc_lists,
        do_root_path_prefix, # must be last
    )
    doc = BeautifulSoup(html, "html.parser")
    for func in transformers:
        func(doc, source_path)

    src = Path(f"{source_path}.html") if as_html else source_path
    output_path = make_output_path(opt.out, renames, src)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(str(doc))


if __name__ == "__main__":
    opt = parse_args(argparse.ArgumentParser()).parse_args()
    render(opt)

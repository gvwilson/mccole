"""Convert Markdown to HTML."""

import argparse
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
from markdown import markdown
from pathlib import Path
import sys

from .util import find_files, find_key_defs, load_config, load_links, write_file


ALSO_HTML_SUFFIX = {".css", ".js", ".py", ".sql"}

AS_HTML = """\
# {path}
```
{content}```
"""

MARKDOWN_EXTENSIONS = [
    "attr_list",
    "def_list",
    "fenced_code",
    "md_in_html",
    "tables"
]


def build(opt):
    """Main driver."""

    # Setup.
    config = load_config(opt.config)
    config["links_md"] = "\n".join(["", *(f"[{key}]: {url}" for key, url in config["links"].items())])
    skips = config["skips"] | {opt.out}
    env = Environment(loader=FileSystemLoader(opt.templates))

    # Find and build files.
    files = find_files(opt, skips)
    markdown, also_html, others = split_files(files)
    handle_markdown(env, opt, config, markdown)
    handle_also_html(env, opt, config, also_html)
    handle_others(env, opt, config, others)


def choose_template(env, source):
    """Select a template."""
    if source.name == "slides.md":
        return env.get_template("slides.html")
    return env.get_template("page.html")


def do_bibliography_links(doc, source, context):
    """Turn 'b:key' links into bibliography references."""
    for node in doc.select("a[href]"):
        if node["href"].startswith("b:"):
            node["href"] = f"@root/bibliography.html#{node['href'][2:]}"


def do_cross_links(doc, source, context):
    """Fix .md links in HTML."""
    for node in doc.select("a[href]"):
        if node["href"].endswith(".md"):
            node["href"] = node["href"].replace(".md", ".html").lower()
        elif Path(node["href"]).suffix in ALSO_HTML_SUFFIX:
            node["href"] = f"{node['href']}.html"


def do_glossary(doc, source, context):
    """Turn 'g:key' links into glossary references and insert list of terms."""
    seen = set()
    for node in doc.select("a[href]"):
        if node["href"].startswith("g:"):
            key = node["href"][2:]
            node["href"] = f"@root/glossary.html#{key}"
            seen.add(key)
    insert_defined_terms(doc, source, seen, context)


def do_inclusion_classes(doc, source, context):
    """Adjust classes of file inclusions."""
    for node in doc.select("code[data-file]"):
        inc = node["data-file"]
        if ":" in inc:
            inc = inc.split(":")[0]
        language = f"language-{Path(inc).suffix.lstrip('.')}"
        node["class"] = language
        node.parent["class"] = language


def do_title(doc, source, context):
    """Make sure title element is filled in."""
    try:
        doc.title.string = doc.h1.get_text()
    except Exception:
        print(f"{source} lacks H1 heading", file=sys.stderr)
        sys.exit(1)


def do_root_path_prefix(doc, source, context):
    """Fix @root links in HTML."""
    depth = len(source.parents) - 1
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


def handle_also_html(env, opt, config, files):
    """Handle files that are also saved as HTML files."""
    for path, info in files.items():
        output_path = make_output_path(opt.out, config["renames"], path)
        write_file(output_path, info["content"])

        embedded = AS_HTML.format(path=path, content=info["content"])
        embedded = render_markdown(env, opt, config["links_md"], path, embedded)
        write_file(Path(f"{output_path}.html"), str(embedded))


def handle_markdown(env, opt, config, files):
    """Handle Markdown files."""
    # Extract cross-reference keys.
    context = {
        "bibliography": find_key_defs(files, "bibliography"),
        "glossary": find_key_defs(files, "glossary"),
    }

    # Render all documents.
    for path, info in files.items():
        info["doc"] = render_markdown(env, opt, config["links_md"], path, info["content"], context)

    # Save results.
    for path, info in files.items():
        output_path = make_output_path(opt.out, config["renames"], path)
        write_file(output_path, str(info["doc"]))


def handle_others(env, opt, config, files):
    """Handle copy-only files."""
    for path, info in files.items():
        output_path = make_output_path(opt.out, config["renames"], path)
        write_file(output_path, info["content"])


def insert_defined_terms(doc, source, seen, context):
    """Insert list of defined terms."""
    target = doc.select("p#terms")
    if not target:
        return
    assert len(target) == 1, f"Duplicate p#terms in {source}"
    target = target[0]
    if not seen:
        target.decompose()
        return
    glossary = {key: context["glossary"][key] for key in seen}
    glossary = {k: v for k, v in sorted(glossary.items(), key=lambda item: item[1].lower())}
    target.append("Terms defined: ")
    for i, (key, term) in enumerate(glossary.items()):
        if i > 0:
            target.append(", ")
        ref = doc.new_tag("a", href=f"@root/glossary.html#{key}")
        ref.string = term
        target.append(ref)


def make_output_path(output_dir, renames, source):
    """Build output path."""
    if source.name in renames:
        source = Path(source.parent, renames[source.name])
    source = Path(str(source).replace(".md", ".html"))
    return Path(output_dir, source)


def parse_args(parser):
    """Parse command-line arguments."""
    parser.add_argument("--config", type=str, default="pyproject.toml", help="optional configuration file")
    parser.add_argument("--css", type=str, help="CSS file")
    parser.add_argument("--icon", type=str, help="icon file")
    parser.add_argument("--out", type=str, default="docs", help="output directory")
    parser.add_argument("--root", type=str, default=".", help="root directory")
    parser.add_argument("--templates", type=str, default="templates", help="templates directory")


def render_markdown(env, opt, links, source, content, context={}):
    """Convert Markdown to HTML."""
    # Generate HTML.
    template = choose_template(env, source)
    content += links
    html = markdown(content, extensions=MARKDOWN_EXTENSIONS)
    html = template.render(content=html, css_file=opt.css, icon_file=opt.icon)

    # Apply transforms if always required or if context provided.
    transformers = (
        (False, do_bibliography_links),
        (False, do_cross_links),
        (False, do_glossary),
        (False, do_inclusion_classes),
        (True, do_title),
        (True, do_root_path_prefix), # must be last
    )
    doc = BeautifulSoup(html, "html.parser")
    for is_required, func in transformers:
        if context or is_required:
            func(doc, source, context)

    return doc


def split_files(files):
    """Divide files into categories."""
    markdown = {}
    also_html = {}
    others = {}
    for path, info in files.items():
        if path.suffix == ".md":
            markdown[path] = info
        elif path.suffix in ALSO_HTML_SUFFIX:
            also_html[path] = info
        else:
            others[path] = info
    return markdown, also_html, others


if __name__ == "__main__":
    opt = parse_args(argparse.ArgumentParser()).parse_args()
    build(opt)

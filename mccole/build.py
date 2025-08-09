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


def build(opt):
    """Main driver."""
    opt.settings = _load_config(opt.config)
    files = _find_files(opt)
    markdown, others = _separate_files(files)
    opt._glossary = _load_glossary(markdown)
    opt.dst.mkdir(parents=True, exist_ok=True)
    _handle_markdown(opt, markdown)
    _handle_others(opt, others)


def construct_parser(parser):
    """Parse command-line arguments."""
    parser.add_argument("--config", default="pyproject.toml", help="configuration file")
    parser.add_argument("--dst", type=Path, default="docs", help="output directory")
    parser.add_argument("--src", type=Path, default=".", help="source directory")
    parser.add_argument(
        "--templates", type=Path, default="templates", help="templates directory"
    )


def _do_bibliography_links(opt, dest, doc):
    """Handle 'b:' bibliography links."""
    for node in doc.select("a[href]"):
        if not node["href"].startswith("b:"):
            continue
        assert node["href"].count(":") == 1
        key = node["href"].split(":")[1]
        node.string = key
        node["href"] = _make_root_prefix(opt, dest) + f"bibliography/#{key}"


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

    keys = {node["href"].split("#")[-1] for node in doc.select("a[href]") if "/glossary/#" in node["href"]}
    if not keys:
        target.decompose()
        return

    entries = [(key, opt._glossary.get(key, "UNDEFINED")) for key in keys]
    entries.sort(key=lambda item: item[1])
    target.append("Terms defined: ")
    for (i, (key, term)) in enumerate(entries):
        tag = doc.new_tag("a", href=key)
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
    return [
        path for path in Path(opt.src).glob("**/*.*") if _is_interesting_file(opt, path)
    ]


def _handle_markdown(opt, files):
    """Handle Markdown files."""
    env = Environment(loader=FileSystemLoader(opt.templates))
    for source in files:
        dest = _make_output_path(opt, source)
        html = _render_markdown(opt, env, source, dest)
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


def _load_config(filename):
    """Read configuration data."""
    config = tomli.loads(Path(filename).read_text())

    if ("tool" not in config) or ("mccole" not in config["tool"]):
        _warn(f"configuration file {filename} does not have 'tool.mccole'")
        return {"skips": set()}

    config = config["tool"]["mccole"]
    config["skips"] = set(config["skips"]) if "skips" in config else set()

    overlap = set(BOILERPLATE.keys()) & config["skips"]
    if overlap:
        _warn(
            f"overlap between skips and renames in config {filename}: {', '.join(sorted(overlap))}"
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


def _render_markdown(opt, env, source, dest):
    """Convert Markdown to HTML."""
    content = source.read_text()
    template = env.get_template("page.html")
    raw_html = markdown(content, extensions=MARKDOWN_EXTENSIONS)
    rendered_html = template.render(content=raw_html)

    doc = BeautifulSoup(rendered_html, "html.parser")
    for func in [
        _do_bibliography_links,
        _do_glossary_links,
        _do_glossary_terms,
        _do_markdown_links,
        _do_pre_code_classes,
        _do_root_links,
        _do_title,
    ]:
        func(opt, dest, doc)

    return str(doc)


def _separate_files(files):
    """Divide files into categories."""
    markdown = [path for path in files if path.suffix == ".md"]
    others = [path for path in files if path.suffix != ".md"]
    return markdown, others


def _warn(msg):
    """Print warning."""
    print(msg, file=sys.stderr)

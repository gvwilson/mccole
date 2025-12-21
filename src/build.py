"""Build site."""

from pathlib import Path

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
from markdown import markdown
import tomli

from . import util


HOME_PAGE = Path("README.md")
GLOSSARY_PATH = Path("glossary") / "index.md"
TEMPLATE_DIR = "templates"
TEMPLATE_PAGE = "page.html"
TEMPLATE_SLIDES = "slides.html"

STANDARD_FILES = {
    "README.md": "",
    "CODE_OF_CONDUCT.md": "conduct",
    "CONTRIBUTING.md": "contributing",
    "LICENSE.md": "license",
}
REVERSE_FILES = {value: key for key, value in STANDARD_FILES.items() if value != ""}

MARKDOWN_EXTENSIONS = ["attr_list", "def_list", "fenced_code", "md_in_html", "tables"]


def build(options):
    """Build the site."""
    config = _load_configuration(options)
    env = Environment(loader=FileSystemLoader(config["templates"]))
    section_slugs, slides, others = _find_files(config)

    _build_page(config, env, None, config["src"] / config["home_page"])
    for slug in section_slugs:
        _build_page(config, env, slug, config["order"][slug]["filepath"])
    for filepath in slides:
        _build_page(config, env, None, filepath)
    for filepath in others:
        _build_other(config, filepath)


def _build_page(config, env, slug, src_path):
    """Handle a Markdown file."""
    content = src_path.read_text()
    with_links = f"{content}\n\n{config['links']}"
    raw_html = markdown(with_links, extensions=MARKDOWN_EXTENSIONS)

    template_name = TEMPLATE_SLIDES if src_path.name == "slides.md" else TEMPLATE_PAGE
    template = env.get_template(template_name)
    context = _make_context(config, slug)
    rendered_html = template.render(content=raw_html, **context)

    doc = BeautifulSoup(rendered_html, "html.parser")
    dst_path = _make_output_path(config, src_path, suffix=".html")
    for func in [
        _patch_terms_defined,  # must be before _patch_glossary_links
        _patch_bibliography_links,
        _patch_figure_numbers,
        _patch_glossary_links,
        _patch_pre_code_classes,
        _patch_table_numbers,
        _patch_title,
        _patch_root_links,  # must be last
    ]:
        func(config, dst_path, doc)

    dst_path.write_text(str(doc))


def _build_other(config, src_path):
    """Handle non-Markdown file."""
    dst_path = _make_output_path(config, src_path)
    dst_path.write_bytes(src_path.read_bytes())


def _collect_figure_numbers(dst_path, doc):
    """Number figures and return IDs."""
    prefix = "f:"
    known = {}
    for i, node in enumerate(doc.select("figure")):
        num = i + 1

        if "id" not in node.attrs:
            util.warn(f"figure {num} in {dst_path} has no ID")
            continue

        if not node["id"].startswith(prefix):
            util.warn(
                f"figure {num} ID {node['id']} in {dst_path} does not start with '{prefix}'"
            )
            continue

        all_captions = node.select("figcaption")
        if len(all_captions) != 1:
            util.warn(
                f"figure {num} ID {node['id']} in {dst_path} has missing/too many figcaption"
            )
            continue

        known[node["id"]] = num
        caption = all_captions[0]
        caption.insert(0, f"Figure {num}: ")

    return known


def _collect_table_numbers(dst_path, doc):
    """Number tables and return IDs."""
    prefix = "t:"
    known = {}
    num = 1
    for node in doc.select("div"):
        if ("id" not in node.attrs) or (not node["id"].startswith(prefix)):
            continue

        if "data-caption" not in node.attrs:
            util.warn(
                f"table div {num} ID {node['id']} in {dst_path} has no data-caption"
            )
            continue

        all_tables = node.select("table")
        if len(all_tables) != 1:
            util.warn(
                f"table div {num} ID {node['id']} in {dst_path} has missing/too many tables"
            )
            continue

        table = all_tables[0]
        caption = doc.new_tag("caption")
        caption.string = f"Table {num}: {node['data-caption']}"
        table.insert(0, caption)
        known[node["id"]] = num
        num += 1

    return known


def _fill_element_numbers(dst_path, doc, prefix, known, text):
    """Fill in cross-reference numbers."""
    for node in doc.select("a[href]"):
        if not node["href"].startswith(prefix):
            continue

        key = node["href"].lstrip("#")
        if key not in known:
            util.warn(f"unknown cross-reference {key} in {dst_path}")
            continue

        node.string = f"{text} {known[key]}"


def _find_files(config):
    """Find section files and other files."""
    order = config["order"]
    slugs = set(order.keys())

    slides = {f for f in config["src"].glob("*/slides.md")}

    excludes = {config["src"] / config["home_page"]}
    excludes |= {value["filepath"] for value in config["order"].values()}
    excludes |= slides

    others = {
        f
        for f in config["src"].glob("*/**")
        if _is_interesting_file(config, excludes, f)
    }
    return slugs, slides, others


def _get_slug_from_link(raw):
    """Convert '@/something/' to 'something'."""
    assert raw.startswith("@/") and raw.endswith("/")
    return raw[2:-1]


def _is_interesting_file(config, excludes, filepath):
    """Is this file worth copying over?"""
    if not filepath.is_file():
        return False

    if filepath in excludes:
        return False

    relative = filepath.relative_to(config["src"])
    if str(relative).startswith("."):
        return False
    if filepath.samefile(config["config"]):
        return False
    if filepath.is_relative_to(config["dst"]):
        return False
    if filepath.is_relative_to(config["extras"]):
        return False
    if filepath.is_relative_to(config["templates"]):
        return False

    for s in config["skips"]:
        if filepath.match(s):
            return False
        if s.endswith("/**") and relative.is_relative_to(s.replace("/**", "")):
            return False

    return True


def _load_configuration(options):
    """Load configuration and combine with options."""
    config_path = options.src / options.config
    config = tomli.loads(config_path.read_text())

    links = util.load_links(options.src)
    glossary = _load_glossary(options.src)

    home_page = options.root
    order = _load_order(options.src, home_page)

    return {
        "config": config_path,
        "dst": options.dst,
        "extras": options.src / util.EXTRAS_DIR,
        "glossary": glossary,
        "home_page": home_page,
        "links": links,
        "order": order,
        "src": options.src,
        "templates": options.src / TEMPLATE_DIR,
        "verbose": options.verbose,
        **config.get("tool", {}).get("mccole", {}),
    }


def _load_glossary(src_path):
    """Load glossary keys and terms."""
    md = (src_path / GLOSSARY_PATH).read_text()
    html = markdown(md, extensions=MARKDOWN_EXTENSIONS)
    doc = BeautifulSoup(html, "html.parser")
    return {node["id"]: node.decode_contents() for node in doc.select("span[id]")}


def _load_order(src_path, home_page):
    """Determine section order from home page file."""
    md = (src_path / home_page).read_text()
    html = markdown(md, extensions=MARKDOWN_EXTENSIONS)
    doc = BeautifulSoup(html, "html.parser")
    lessons = _load_order_section(doc, "lessons", lambda i: str(i + 1))
    appendices = _load_order_section(doc, "appendices", lambda i: chr(ord("A") + i))
    combined = {**lessons, **appendices}

    flattened = list(combined.keys())
    for i, slug in enumerate(flattened):
        combined[slug]["previous"] = flattened[i - 1] if i > 0 else None
        combined[slug]["next"] = flattened[i + 1] if i < (len(flattened) - 1) else None
        combined[slug]["filepath"] = src_path / REVERSE_FILES.get(
            slug, Path(slug) / "index.md"
        )

    return combined


def _load_order_section(doc, selector, labeller):
    """Load a section of the table of contents from README.md DOM."""
    div = f"div#{selector}"
    return {
        _get_slug_from_link(node["href"]): {
            "number": labeller(i),
            "kind": selector,
            "title": node.decode_contents(),
        }
        for i, node in enumerate(doc.select(div)[0].select("a[href]"))
    }


def _make_context(config, slug):
    """Make rendering context for a particular file."""
    order = config["order"]
    context = {
        "lessons": [
            (slug, entry["title"])
            for slug, entry in order.items()
            if entry["kind"] == "lessons"
        ],
        "appendices": [
            (slug, entry["title"])
            for slug, entry in order.items()
            if entry["kind"] == "appendices"
        ],
    }

    if slug is None:
        prev_link = None
        prev_title = None
        next_link = None
        next_title = None
    else:
        entry = order[slug]
        prev_link = entry["previous"]
        prev_title = None if prev_link is None else order[prev_link]["title"]
        next_link = entry["next"]
        next_title = None if next_link is None else order[next_link]["title"]

    return {"prev": (prev_link, prev_title), "next": (next_link, next_title), **context}


def _make_output_path(config, src_path, suffix=None):
    """Generate output file path."""
    if src_path.name in STANDARD_FILES:
        dst_path = config["dst"] / STANDARD_FILES[src_path.name] / "index.md"
    elif src_path.name == config["home_page"].name:
        dst_path = config["dst"] / "index.md"
    else:
        dst_path = config["dst"] / src_path.relative_to(config["src"])
    if suffix is not None:
        dst_path = dst_path.with_suffix(suffix)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    return dst_path


def _make_root_prefix(config, path):
    """Create prefix to root for path."""
    relative = path.relative_to(config["dst"])
    depth = len(relative.parents) - 1
    assert depth >= 0
    return "./" if (depth == 0) else "../" * depth


def _patch_bibliography_links(config, dst_path, doc):
    """Convert b: bibliography links."""
    _patch_special_link(config, dst_path, doc, "b:", "bibliography", True)


def _patch_figure_numbers(config, dst_path, doc):
    """Insert figure numbers."""
    known = _collect_figure_numbers(dst_path, doc)
    _fill_element_numbers(dst_path, doc, "#f:", known, "Figure")


def _patch_glossary_links(config, dst_path, doc):
    """Convert g: glossary links."""
    _patch_special_link(config, dst_path, doc, "g:", "glossary", False)


def _patch_pre_code_classes(config, dst_path, doc):
    """Add language classes to <pre> elements."""
    for node in doc.select("pre>code"):
        cls = node.get("class", [])
        node.parent["class"] = node.parent.get("class", []) + cls


def _patch_root_links(config, dst_path, doc):
    """Convert @ links to relative path to root."""
    prefix = _make_root_prefix(config, dst_path)
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


def _patch_special_link(config, dst_path, doc, prefix, stem, change_text):
    """Patch specially-prefixed links."""
    for node in doc.select("a[href]"):
        if not node["href"].startswith(prefix):
            continue
        assert node["href"].count(":") == 1
        key = node["href"].split(":")[1]
        if change_text:
            node.string = key
        node["href"] = _make_root_prefix(config, dst_path) + f"{stem}/#{key}"


def _patch_table_numbers(config, dst_path, doc):
    """Insert figure numbers."""
    known = _collect_table_numbers(dst_path, doc)
    _fill_element_numbers(dst_path, doc, "#t:", known, "Table")


def _patch_terms_defined(config, dst_path, doc):
    """Insert terms defined where requested."""
    paragraphs = doc.select("p#terms")
    if not paragraphs:
        return
    if len(paragraphs) > 1:
        util.warn(f"{dst_path} has multiple p#terms")
        return
    para = paragraphs[0]

    keys = {
        node["href"] for node in doc.select("a[href]") if node["href"].startswith("g:")
    }
    if not keys:
        para.decompose()
        return

    entries = [(key, config["glossary"].get(key, "UNDEFINED")) for key in keys]
    entries.sort(key=lambda item: item[1])
    para.append("Terms defined: ")
    for i, (key, term) in enumerate(entries):
        tag = doc.new_tag("a", attrs={"class": "term-defined"}, href=key)
        tag.string = term
        if i > 0:
            para.append(", ")
        para.append(tag)


def _patch_title(config, dst_path, doc):
    """Make sure the HTML title element is set."""
    if doc.title is None:
        util.warn(f"{dst_path} does not have <title> element")
        return
    try:
        doc.title.string = doc.h1.get_text()
    except Exception:
        util.warn(f"{dst_path} lacks H1 heading")

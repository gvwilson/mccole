"""Build site."""

from pathlib import Path

from bs4 import BeautifulSoup
import frontmatter as fm
from jinja2 import Environment, FileSystemLoader
from markdown import markdown
import sys
import tomli

from .inclusions import patch_inclusions
from .shortcodes import process_shortcodes
from .index_build import build_index_page
from . import util


HOME_PAGE = Path("README.md")
GLOSSARY_PATH = Path("glossary") / "index.md"
BIBLIOGRAPHY_PATH = Path("bibliography") / "index.md"
INDEX_PATH = Path("index") / "index.md"
TEMPLATE_DIR = "_templates"
TEMPLATE_PAGE = "page.html"
TEMPLATE_SLIDES = "slides.html"

STANDARD_FILES = {
    "README.md": "",
    "CODE_OF_CONDUCT.md": "conduct",
    "CONTRIBUTING.md": "contributing",
    "LICENSE.md": "license",
}
REVERSE_FILES = {value: key for key, value in STANDARD_FILES.items() if value != ""}

MARKDOWN_EXTENSIONS = [
    "attr_list",
    "codehilite",
    "def_list",
    "fenced_code",
    "md_in_html",
    "tables",
]


def build(options):
    """Build the site."""
    config = _load_configuration(options)
    if options.extra:
        config["extra_html"] = Path(options.extra).read_text(encoding="utf-8")
    env = Environment(loader=FileSystemLoader(config["templates"]))
    section_slugs, slides, others = _find_files(config)

    ix_entries = []

    # Build home page
    _build_page(config, env, None, config["src"] / config["home_page"], ix_entries)

    # Build all section pages EXCEPT the index page (build it last)
    for slug in section_slugs:
        if slug == "index":
            continue
        _build_page(config, env, slug, config["order"][slug]["filepath"], ix_entries)

    # Build slides and other files
    for filepath in slides:
        _build_page(config, env, None, filepath, ix_entries)
    for filepath in others:
        _build_other(config, filepath)

    # Build index page last so all ix_entries from other pages are available
    if "index" in section_slugs and ix_entries:
        _build_index_page(config, env, ix_entries)
    elif "index" in section_slugs:
        _build_page(config, env, "index", config["order"]["index"]["filepath"], ix_entries)


def _build_page(config, env, slug, src_path, ix_entries=None):
    """Handle a Markdown file."""
    if ix_entries is None:
        ix_entries = []

    content = src_path.read_text(encoding="utf-8")

    # Parse frontmatter
    post = fm.loads(content)
    metadata = {k: v for k, v in post.metadata.items() if k != "version"}
    body = post.content

    # Process shortcodes BEFORE markdown conversion
    body_with_links = f"{body}\n\n{config['links']}"
    processed = process_shortcodes(body_with_links, config, src_path, ix_entries)

    # Convert processed text to HTML
    raw_html = markdown(processed, extensions=MARKDOWN_EXTENSIONS)

    template_name = TEMPLATE_SLIDES if src_path.name == "slides.md" else TEMPLATE_PAGE
    template = env.get_template(template_name)
    context = _make_context(config, slug, metadata)
    rendered_html = template.render(content=raw_html, **context)

    doc = BeautifulSoup(rendered_html, "html.parser")
    dst_path = _make_output_path(config, src_path, suffix=".html")
    for func in [
        _patch_terms_defined,  # must be before _patch_glossary_links
        _patch_bibliography_links,
        _patch_figure_numbers,
        _patch_glossary_links,
        patch_inclusions,
        _patch_pre_code_classes,
        _patch_pre_accessibility,
        _patch_exercise_labels,
        _patch_table_numbers,
        _patch_th_scope,
        _patch_title,
        _patch_markdown_attribute,  # must be at the end
        _patch_root_links,  # must be at the end
    ]:
        func(config, src_path, dst_path, doc)

    try:
        dst_path.write_text(str(doc), encoding="utf-8")
    except Exception as exc:
        print(f"unable to write {dst_path} because {exc}")
        sys.exit(1)


def _build_index_page(config, env, ix_entries):
    """Build the index page from collected ix_entries."""
    slug = "index"
    src_path = config["order"][slug]["filepath"]

    # Generate index Markdown content from collected entries
    index_content = build_index_page(ix_entries, config)

    # Read frontmatter from existing index file if it exists
    if src_path.exists():
        post = fm.loads(src_path.read_text(encoding="utf-8"))
        metadata = {k: v for k, v in post.metadata.items() if k != "version"}
    else:
        metadata = {"title": "Index"}

    template = env.get_template(TEMPLATE_PAGE)
    context = _make_context(config, slug, metadata)

    raw_html = markdown(index_content, extensions=MARKDOWN_EXTENSIONS)
    rendered_html = template.render(content=raw_html, **context)

    doc = BeautifulSoup(rendered_html, "html.parser")
    dst_path = _make_output_path(config, src_path, suffix=".html")

    for func in [
        _patch_terms_defined,
        _patch_bibliography_links,
        _patch_figure_numbers,
        _patch_glossary_links,
        patch_inclusions,
        _patch_pre_code_classes,
        _patch_pre_accessibility,
        _patch_exercise_labels,
        _patch_table_numbers,
        _patch_th_scope,
        _patch_title,
        _patch_markdown_attribute,
        _patch_root_links,
    ]:
        func(config, src_path, dst_path, doc)

    try:
        dst_path.write_text(str(doc), encoding="utf-8")
    except Exception as exc:
        print(f"unable to write {dst_path} because {exc}")
        sys.exit(1)


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
    if any(filepath.is_relative_to(x) for x in [config["dst"], config["extras"], config["templates"]]):
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
    config = tomli.loads(config_path.read_text(encoding="utf-8"))

    links = util.load_links(options.src)
    glossary = _load_glossary(options.src)

    home_page = options.root
    order = _load_order(options.src, home_page)

    mccole_config = config.get("tool", {}).get("mccole", {})
    book_title = mccole_config.get("title", _load_book_title(options.src, home_page))

    return {
        "book_title": book_title,
        "config": config_path,
        "dst": options.dst,
        "extras": options.src / util.EXTRAS_DIR,
        "forma": options.forma,
        "glossary": glossary,
        "home_page": home_page,
        "links": links,
        "math": options.math,
        "order": order,
        "src": options.src,
        "templates": options.src / TEMPLATE_DIR,
        "verbose": options.verbose,
        **mccole_config,
    }


def _load_book_title(src_path, home_page):
    """Extract the H1 title from the home page as the book title."""
    try:
        md = (src_path / home_page).read_text(encoding="utf-8")
        post = fm.loads(md)
        html = markdown(post.content, extensions=MARKDOWN_EXTENSIONS)
        doc = BeautifulSoup(html, "html.parser")
        h1 = doc.find("h1")
        return h1.get_text() if h1 else ""
    except Exception:
        return ""


def _load_glossary(src_path):
    """Load glossary keys and terms."""
    md = (src_path / GLOSSARY_PATH).read_text(encoding="utf-8")
    html = markdown(md, extensions=MARKDOWN_EXTENSIONS)
    doc = BeautifulSoup(html, "html.parser")
    return {node["id"]: node.decode_contents() for node in doc.select("span[id]")}


def _load_order(src_path, home_page):
    """Determine section order from home page file."""
    md = (src_path / home_page).read_text(encoding="utf-8")
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


def _make_context(config, slug, metadata=None):
    """Make rendering context for a particular file."""
    if metadata is None:
        metadata = {}
    order = config["order"]
    # Use a local variable name to avoid shadowing the parameter 'slug'
    context = {
        "lessons": [
            (s, entry["title"])
            for s, entry in order.items()
            if entry["kind"] == "lessons"
        ],
        "appendices": [
            (s, entry["title"])
            for s, entry in order.items()
            if entry["kind"] == "appendices"
        ],
    }

    if slug is None:
        prev_link = None
        prev_title = None
        next_link = None
        next_title = None
        context["chapter_number"] = None
        context["chapter_kind"] = None
    else:
        entry = order[slug]
        prev_link = entry["previous"]
        prev_title = None if prev_link is None else order[prev_link]["title"]
        next_link = entry["next"]
        next_title = None if next_link is None else order[next_link]["title"]
        context["chapter_number"] = entry["number"]
        context["chapter_kind"] = entry["kind"]

    # Merge frontmatter metadata into context (page-level title, syllabus, etc.)
    context.update(metadata)

    # Always expose book_title (site-wide title from config)
    context.setdefault("book_title", config.get("book_title", ""))

    # Expose language code so the <html lang="..."> attribute can be set per book
    context.setdefault("lang", config.get("lang", "en"))

    # description falls back to book_title if not set in page frontmatter
    context.setdefault("description", config.get("description", context.get("book_title", "")))

    # Expose current slug so the nav template can mark the active page
    context["current_slug"] = slug
    context["extra_html"] = config.get("extra_html", "")
    context["forma"] = config.get("forma", False)
    context["math"] = config.get("math", False)

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


def _patch_bibliography_links(config, src_path, dst_path, doc):
    """Convert b: bibliography links."""
    _patch_special_link(config, src_path, dst_path, doc, "b:", "bibliography", True)


def _patch_figure_numbers(config, src_path, dst_path, doc):
    """Insert figure numbers."""
    known = _collect_figure_numbers(dst_path, doc)
    _fill_element_numbers(dst_path, doc, "#f:", known, "Figure")


def _patch_glossary_links(config, src_path, dst_path, doc):
    """Convert g: glossary links."""
    _patch_special_link(config, src_path, dst_path, doc, "g:", "glossary", False)


def _patch_markdown_attribute(config, src_path, dst_path, doc):
    """Remove markdown='1' attribute."""
    for node in doc.select("[markdown]"):
        del node["markdown"]


def _patch_exercise_labels(config, src_path, dst_path, doc):
    """Add aria-label to exercise sections so screen reader landmark navigation works."""
    for node in doc.select("section.exercises"):
        if not node.get("aria-label"):
            node["aria-label"] = "Exercises"


def _patch_pre_accessibility(config, src_path, dst_path, doc):
    """Make scrollable <pre> blocks keyboard-focusable and label them with their language."""
    for node in doc.select("pre"):
        node["tabindex"] = "0"
        # Extract language from class like "language-python" → "python"
        classes = node.get("class", [])
        for cls in classes:
            if cls.startswith("language-"):
                node["data-lang"] = cls[len("language-"):]
                break


def _patch_pre_code_classes(config, src_path, dst_path, doc):
    """Add language classes to <pre> elements."""
    for node in doc.select("pre>code"):
        cls = node.get("class", [])
        node.parent["class"] = node.parent.get("class", []) + cls


def _patch_th_scope(config, src_path, dst_path, doc):
    """Add scope attributes to <th> elements for screen reader table navigation."""
    for node in doc.select("thead th"):
        if not node.get("scope"):
            node["scope"] = "col"
    for node in doc.select("tbody th"):
        if not node.get("scope"):
            node["scope"] = "row"


def _patch_root_links(config, src_path, dst_path, doc):
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


def _patch_special_link(config, src_path, dst_path, doc, prefix, stem, change_text):
    """Patch specially-prefixed links."""
    for node in doc.select("a[href]"):
        if not node["href"].startswith(prefix):
            continue
        assert node["href"].count(":") == 1
        key = node["href"].split(":")[1]
        if change_text:
            node.string = key
        node["href"] = _make_root_prefix(config, dst_path) + f"{stem}/#{key}"


def _patch_table_numbers(config, src_path, dst_path, doc):
    """Insert figure numbers."""
    known = _collect_table_numbers(dst_path, doc)
    _fill_element_numbers(dst_path, doc, "#t:", known, "Table")


def _patch_terms_defined(config, src_path, dst_path, doc):
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

    keys = {k[2:] for k in keys}
    entries = [(key, config["glossary"].get(key, "UNDEFINED")) for key in keys]
    entries.sort(key=lambda item: item[1])
    para.append("Terms defined: ")
    for i, (key, term) in enumerate(entries):
        tag = doc.new_tag(
            "a", attrs={"class": "term-defined"}, href=f"@/glossary/#{key}"
        )
        tag.string = term
        if i > 0:
            para.append(", ")
        para.append(tag)


def _patch_title(config, src_path, dst_path, doc):
    """Make sure the HTML title element is set."""
    if doc.title is None:
        util.warn(f"{dst_path} does not have <title> element")
        return
    h1 = doc.find("h1")
    if h1:
        doc.title.string = h1.get_text()
    else:
        util.warn(f"{dst_path} lacks H1 heading")

"""Build single-page version of site."""

from pathlib import Path
from bs4 import BeautifulSoup

from .build import _build_page_fragment
from . import util

SINGLE_PAGE_TEMPLATE = "single_page.html"


def build_single_page(config, env, output_path):
    """Assemble all pages into a single HTML file at output_path."""
    ix_entries = []

    # Home page as preamble div
    home_src = config["src"] / config["home_page"]
    home_metadata, _, home_doc = _build_page_fragment(config, env, None, home_src, ix_entries)
    home_main = home_doc.find("main")
    home_html = ""
    if home_main:
        _rewrite_special_links(home_main)
        _rewrite_at_links(home_main)
        home_html = home_main.decode_contents()

    # Chapter/appendix sections in order
    sections = []
    for slug, entry in config["order"].items():
        if slug == "index":
            continue
        src_path = entry["filepath"]
        chapter_number = entry["number"]

        metadata, dst_path, doc = _build_page_fragment(config, env, slug, src_path, [])
        main = doc.find("main")
        if main is None:
            util.warn(f"single-page: no <main> in {src_path}")
            continue

        # Compound figure and table numbering (before ID namespacing)
        _apply_compound_figure_numbers(main, dst_path, chapter_number)
        _apply_compound_table_numbers(main, dst_path, chapter_number)

        # Namespace intra-page #anchor hrefs before IDs are renamed
        _namespace_intrapage_hrefs(main, slug)

        # Namespace all id attributes
        _namespace_ids(main, slug)

        # Rewrite g: / b: special-prefix links
        _rewrite_special_links(main)

        # Rewrite @/ links to in-page anchors or root-relative paths
        _rewrite_at_links(main)

        # Remove the template-inserted <h1> (page title); content headings shift up
        h1 = main.find("h1")
        if h1:
            h1.decompose()
        _bump_headings(main)

        # Prefix chapter-local image paths with slug/
        _rewrite_image_paths(main, slug)

        sections.append({
            "slug": slug,
            "chapter_number": chapter_number,
            "title": entry.get("title", slug),
            "kind": entry["kind"],
            "html": main.decode_contents(),
        })

    template = env.get_template(SINGLE_PAGE_TEMPLATE)
    rendered = template.render(
        home_html=home_html,
        sections=sections,
        book_title=config.get("book_title", ""),
        lang=config.get("lang", "en"),
        math=config.get("math", False),
        extra_html=config.get("extra_html", ""),
        forma=config.get("forma", False),
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")


def _apply_compound_figure_numbers(main, dst_path, chapter_number):
    """Number figures as chapter_number.N and fill cross-ref link text."""
    known = {}
    for num, node in enumerate(main.select("figure"), start=1):
        if "id" not in node.attrs:
            util.warn(f"figure {num} in {dst_path} has no ID")
            continue
        if not node["id"].startswith("f:"):
            util.warn(f"figure ID {node['id']} in {dst_path} does not start with 'f:'")
            continue
        captions = node.select("figcaption")
        if len(captions) != 1:
            util.warn(f"figure {node['id']} in {dst_path} has missing/too many figcaption")
            continue
        label = f"{chapter_number}.{num}"
        known[node["id"]] = label
        captions[0].insert(0, f"Figure {label}: ")

    for node in main.select("a[href]"):
        if not node["href"].startswith("#f:"):
            continue
        key = node["href"][1:]  # strip leading #
        if key in known:
            node.string = f"Figure {known[key]}"
        else:
            util.warn(f"unknown figure cross-reference {key} in {dst_path}")


def _apply_compound_table_numbers(main, dst_path, chapter_number):
    """Number tables as chapter_number.N and fill cross-ref link text."""
    factory = BeautifulSoup("", "html.parser")
    known = {}
    for num, node in enumerate(main.select("div[id^='t:']"), start=1):
        if "data-caption" not in node.attrs:
            util.warn(f"table {node['id']} in {dst_path} has no data-caption")
            continue
        tables = node.select("table")
        if len(tables) != 1:
            util.warn(f"table {node['id']} in {dst_path} has missing/too many tables")
            continue
        label = f"{chapter_number}.{num}"
        known[node["id"]] = label
        caption = factory.new_tag("caption")
        caption.string = f"Table {label}: {node['data-caption']}"
        tables[0].insert(0, caption)

    for node in main.select("a[href]"):
        if not node["href"].startswith("#t:"):
            continue
        key = node["href"][1:]  # strip leading #
        if key in known:
            node.string = f"Table {known[key]}"
        else:
            util.warn(f"unknown table cross-reference {key} in {dst_path}")


def _namespace_intrapage_hrefs(main, slug):
    """Prefix all #anchor hrefs with slug-- to match namespaced IDs."""
    for node in main.select("a[href]"):
        href = node["href"]
        if href.startswith("#"):
            node["href"] = f"#{slug}--{href[1:]}"


def _namespace_ids(main, slug):
    """Prefix every id attribute with slug--."""
    for node in main.find_all(id=True):
        node["id"] = f"{slug}--{node['id']}"


def _rewrite_special_links(main):
    """Rewrite g:key -> #glossary--key and b:key -> #bibliography--key."""
    for node in main.select("a[href]"):
        href = node["href"]
        if href.startswith("g:"):
            node["href"] = f"#glossary--{href[2:]}"
        elif href.startswith("b:"):
            node["href"] = f"#bibliography--{href[2:]}"


def _rewrite_at_links(main):
    """Rewrite @/ links to in-page anchors or root-relative paths."""
    for node in main.select("a[href]"):
        href = node["href"]
        if not href.startswith("@/"):
            continue
        path = href[2:]  # strip @/
        if not path or path == "/":
            node["href"] = "#home"
        elif path.startswith("glossary/"):
            anchor = path.split("#", 1)[1] if "#" in path else ""
            node["href"] = f"#glossary--{anchor}" if anchor else "#glossary"
        elif path.startswith("bibliography/"):
            anchor = path.split("#", 1)[1] if "#" in path else ""
            node["href"] = f"#bibliography--{anchor}" if anchor else "#bibliography"
        elif "#" in path:
            # @/slug/#anchor -> #slug--anchor (target IDs are namespaced with their slug)
            target_slug, anchor = path.split("#", 1)
            target_slug = target_slug.strip("/")
            node["href"] = f"#{target_slug}--{anchor}"
        else:
            # @/slug/ -> #slug
            node["href"] = f"#{path.strip('/')}"

    # Strip @/ from img src (e.g. @/_static/...) to make root-relative
    for node in main.select("img[src]"):
        src = node["src"]
        if src.startswith("@/"):
            node["src"] = src[2:]


def _bump_headings(main):
    """Shift h5->h6, h4->h5, h3->h4, h2->h3, h1->h2 (descending to avoid double-bumping)."""
    for level in range(5, 0, -1):
        for node in main.find_all(f"h{level}"):
            node.name = f"h{level + 1}"


def _rewrite_image_paths(main, slug):
    """Prefix chapter-local image src values with slug/ so they resolve from the site root."""
    absolute_prefixes = ("http://", "https://", "//", "/", "_static/", "data:")
    for node in main.select("img[src]"):
        src = node["src"]
        if not any(src.startswith(p) for p in absolute_prefixes):
            node["src"] = f"{slug}/{src}"

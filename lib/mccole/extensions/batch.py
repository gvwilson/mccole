"""Initialization required by template."""

import ark
from datetime import datetime
from pathlib import Path
import shortcodes
from shutil import copyfile

import util


@ark.events.register(ark.events.Event.INIT_BUILD)
def init_build():
    """Launch startup tasks in order."""
    _init_date()
    _collect_metadata()
    _decorate_metadata()
    _collect_targets()


@ark.events.register(ark.events.Event.EXIT_BUILD)
def exit_build():
    """Run finalization tasks in order."""
    _copy_files()


@ark.filters.register(ark.filters.Filter.LOAD_NODE_FILE)
def filter_files(value, filepath):
    """Only process HTML and Markdown files."""
    result = filepath.suffix in {".html", ".md"}
    return result


def _collect_metadata():
    """Collect all metadata from nodes."""
    metadata = {}

    def _visitor(node):
        slug = node.slug if node.slug else "@root"
        metadata[slug] = node.meta

    ark.nodes.root().walk(_visitor)
    ark.site.config["_meta_"] = metadata


def _collect_targets():
    """Collect targets of numbered cross-references."""

    # Collect data from a figure.
    def _collect_figures(pargs, kwargs, extra):
        util.require(
            "slug" in kwargs,
            f"Bad 'figure' in {extra['filename']}: '{pargs}' and '{kwargs}'",
        )
        extra["figures"].append(kwargs["slug"])

    # Collect data from a table.
    def _collect_tables(pargs, kwargs, extra):
        util.require(
            "slug" in kwargs,
            f"Bad 'table' in {extra['filename']}: '{pargs}' and '{kwargs}'",
        )
        extra["tables"].append(kwargs["slug"])

    # Visit each node, collecting data.
    def _visitor(node):
        if (not node.slug) or (node.ext != "md"):
            return

        collected = {"filename": node.filepath, "figures": [], "tables": []}
        parser.parse(node.text, collected)
        if node.slug not in collector:
            collector[node.slug] = {"figures": {}, "tables": {}}
        number = ark.site.config["_meta_"][node.slug]["number"]
        collector[node.slug]["figures"].update(
            {
                fig_slug: {"slug": f"{number}.{i + 1}", "node": node.slug}
                for i, fig_slug in enumerate(collected["figures"])
            }
        )
        collector[node.slug]["tables"].update(
            {
                tbl_slug: {"slug": f"{number}.{i + 1}", "node": node.slug}
                for i, tbl_slug in enumerate(collected["tables"])
            }
        )

    parser = shortcodes.Parser(inherit_globals=False, ignore_unknown=True)
    parser.register(_collect_figures, "figure")
    parser.register(_collect_tables, "table")
    collector = {}
    ark.nodes.root().walk(_visitor)
    ark.site.config["_figures_"] = {}
    ark.site.config["_tables_"] = {}
    for slug, seen in collector.items():
        for key, number in seen["figures"].items():
            ark.site.config["_figures_"][key] = number
        for key, number in seen["tables"].items():
            ark.site.config["_tables_"][key] = number


def _copy_files():
    """Copy files from source directories (not recursive)."""
    for pat in ark.site.config["copy"]:
        src_dir = ark.site.src()
        out_dir = ark.site.out()
        for src_file in Path(src_dir).rglob(f"**/{pat}"):
            out_file = str(src_file).replace(src_dir, out_dir)
            Path(out_file).parent.mkdir(exist_ok=True, parents=True)
            copyfile(src_file, out_file)


def _init_date():
    """Add the date to the site configuration object."""
    ark.site.config["_timestamp_"] = datetime.utcnow()


def _decorate_metadata():
    """Number chapters and appendices."""
    metadata = ark.site.config["_meta_"]

    for i, slug in enumerate(ark.site.config["chapters"]):
        metadata[slug]["kind"] = util.kind("chapter")
        metadata[slug]["number"] = str(i + 1)

    for i, slug in enumerate(ark.site.config["appendices"]):
        metadata[slug]["kind"] = util.kind("appendix")
        metadata[slug]["number"] = chr(ord("A") + i)

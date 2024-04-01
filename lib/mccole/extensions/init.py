"""Initialization required by template."""

import ark
from datetime import datetime


# Names of parts.
KIND = {
    "en": {
        "appendix": "Appendix",
        "chapter": "Chapter",
    },
}


@ark.events.register(ark.events.Event.INIT_BUILD)
def init_build():
    """Launch startup tasks in order."""
    _init_date()
    _number_contents()
    _collect_titles()


@ark.filters.register(ark.filters.Filter.LOAD_NODE_FILE)
def filter_files(value, filepath):
    """Only process HTML and Markdown files."""
    result = filepath.suffix in {".html", ".md"}
    return result


def _collect_titles():
    """Gather titles of pages."""
    assert "_number_" in ark.site.config

    def _visitor(node):
        if node.ext != "md":
            return
        if not node.slug:
            return
        assert node.slug in ark.site.config["_number_"]
        ark.site.config["_number_"][node.slug]["title"] = node.meta["title"]

    ark.nodes.root().walk(_visitor)


def _init_date():
    """Add the date to the site configuration object."""
    ark.site.config["_timestamp_"] = datetime.utcnow()


def _number_contents():
    """Number chapters and appendices."""
    lang = ark.site.config["lang"]
    chapters = {
        slug: {"kind": KIND[lang]["chapter"], "number": str(i + 1)}
        for i, slug in enumerate(ark.site.config["chapters"])
    }
    appendices = {
        slug: {"kind": KIND[lang]["appendix"], "number": chr(ord("A") + i)}
        for i, slug in enumerate(ark.site.config["appendices"])
    }
    ark.site.config["_number_"] = chapters | appendices

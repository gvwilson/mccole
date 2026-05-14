"""Replace tabs with spaces in lesson and appendix Markdown files."""

from . import util

# Default number of spaces per tab stop
DEFAULT_TABSIZE = 4


def detab(options):
    """Replace tabs with spaces in lesson and appendix Markdown files."""
    order = util.load_order(options.src, options.root)
    for entry in order.values():
        src_path = entry["filepath"]
        if not src_path.exists():
            continue
        original = src_path.read_text(encoding="utf-8")
        expanded = original.expandtabs(options.tabsize)
        if expanded != original:
            src_path.write_text(expanded, encoding="utf-8")

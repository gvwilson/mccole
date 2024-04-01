"""Table of contents and related cross-references."""

import ark
import shortcodes

import util


@shortcodes.register("toc")
def table_of_contents(pargs, kwargs, node):
    """Handle [% toc %] table of contents shortcode."""
    util.require(
        (not pargs) and (not kwargs),
        f"Bad 'toc' in {node.path}: '{pargs}' and '{kwargs}'",
    )
    chapters = [
        f"<li>{cross_ref([slug], {'kind': 'title'}, node)}</li>"
        for slug in ark.site.config["chapters"]
    ]
    chapters = f'<ol class="toc-chapters">{"".join(chapters)}</ol>'
    appendices = [
        f"<li>{cross_ref([slug], {'kind': 'title'}, node)}</li>"
        for slug in ark.site.config["appendices"]
    ]
    appendices = f'<ol class="toc-appendices">{"".join(appendices)}</ol>'
    return f"{chapters}\n{appendices}"


@shortcodes.register("x")
def cross_ref(pargs, kwargs, node):
    """Handle [%x slug %] cross-reference shortcode."""
    util.require(
        (len(pargs) == 1) and util.allowed(kwargs, {"kind"}),
        f"Bad 'x' in {node.path}: '{pargs}' and '{kwargs}'",
    )
    slug = pargs[0]
    util.require(
        slug in ark.site.config["_number_"],
        f"Unknown cross-reference key '{slug}' in {node.path}",
    )
    if kwargs.get("kind", None) == "title":
        fill = ark.site.config["_number_"][slug]["title"]
    else:
        kind = ark.site.config["_number_"][slug]["kind"]
        number = ark.site.config["_number_"][slug]["number"]
        fill = f"{kind}&nbsp;{number}"
    return f'<a href="@root/{slug}/">{fill}</a>'
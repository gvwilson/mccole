"""McCole template utilities."""

import ark
import markdown
import re
import sys


# Markdown extensions.
MD_EXTENSIONS = [
    "markdown.extensions.extra",
    "markdown.extensions.smarty"
]

# Match inside HTML paragraph markers.
INSIDE_PARAGRAPH = re.compile(r"<p>(.+?)</p>")


def allowed(kwargs, allowed):
    """Check that dictionary keys are a subset of those allowed."""
    return set(kwargs.keys()).issubset(allowed)


def fail(msg):
    """Fail unilaterally."""
    print(msg, file=sys.stderr)
    raise AssertionError(msg)


def markdownify(text, strip_p=True, with_links=False):
    """Convert Markdown to HTML."""
    links = ark.site.config.get("_links_block_", "")
    result = markdown.markdown(f"{text}\n{links}", extensions=MD_EXTENSIONS)
    if strip_p and result.startswith("<p>"):
        result = INSIDE_PARAGRAPH.match(result).group(1)
    return result


def require(cond, msg):
    """Fail if condition untrue."""
    if not cond:
        fail(msg)



"""Shortcode pre-processor: transforms [%tag args%] patterns into HTML before markdown()."""

import re
import shlex

from . import util


# Matches [%tag args%] or [% tag args %] or [%/tag%] (closing tags)
_SHORTCODE_RE = re.compile(r"\[%\s*(/?[a-zA-Z_][a-zA-Z0-9_]*)(.*?)%\]", re.DOTALL)


def process_shortcodes(text, config, src_path, ix_entries):
    """
    Replace shortcodes in text with HTML.

    - config: the build configuration dict (has config["order"] for chapter info)
    - src_path: Path of the current source file
    - ix_entries: a list to APPEND index entries to; each entry is a dict
      {"key": str, "text": str, "slug": str, "uid": str}

    Returns the processed text string.
    """
    # Counter for ix UIDs resets per call
    ix_counter = [0]

    def _replace(match):
        tag = match.group(1)
        args_str = match.group(2).strip()

        # Closing tags are silently stripped
        if tag.startswith("/"):
            return ""

        # Parse args: shlex.split, tokens with '=' are kwargs, others are pargs
        try:
            tokens = shlex.split(args_str)
        except ValueError:
            tokens = args_str.split()

        pargs = []
        kwargs = {}
        for token in tokens:
            if "=" in token:
                key, _, value = token.partition("=")
                kwargs[key.strip()] = value.strip().strip("'\"")
            else:
                pargs.append(token.strip("'\""))

        handler = _HANDLERS.get(tag)
        if handler is None:
            util.warn(f"unknown shortcode [{tag}] in {src_path}")
            return match.group(0)

        return handler(pargs, kwargs, config, src_path, ix_entries, ix_counter)

    return _SHORTCODE_RE.sub(_replace, text)


def _missing_shortcode_arg(tag, name, src_path, default=""):
    """Warn consistently when a shortcode argument is missing."""
    util.warn(f"[%{tag}%] shortcode missing {name} in {src_path}")
    return default


def _page_slug(src_path):
    """Determine the page slug for index entry IDs."""
    return "home" if src_path.name == "README.md" else src_path.parent.name


def _crossref_link(css_class, href, text=""):
    """Build a simple anchor element."""
    return f'<a class="{css_class}" href="{href}">{text}</a>'


# ---------------------------------------------------------------------------
# Individual shortcode handlers
# All have signature: (pargs, kwargs, config, src_path, ix_entries, ix_counter) -> str
# ---------------------------------------------------------------------------


def _handle_b(pargs, kwargs, config, src_path, ix_entries, ix_counter):
    """[%b key1 key2 … %] → bibliography links."""
    if not pargs:
        return _missing_shortcode_arg("b", "keys", src_path)
    parts = [
        _crossref_link("bib-ref", f"@/bibliography/#{key}", key) for key in pargs
    ]
    return "[" + ", ".join(parts) + "]"


def _handle_f(pargs, kwargs, config, src_path, ix_entries, ix_counter):
    """[%f slug %] → figure cross-reference (text filled in by post-processor)."""
    if not pargs:
        return _missing_shortcode_arg("f", "slug", src_path)
    return _crossref_link("fig-ref", f"#f:{pargs[0]}")


def _handle_g(pargs, kwargs, config, src_path, ix_entries, ix_counter):
    """[%g key "text" %] → glossary link."""
    if not pargs:
        return _missing_shortcode_arg("g", "key", src_path)
    key = pargs[0]
    text = pargs[1] if len(pargs) > 1 else key
    return _crossref_link("gl-ref", f"@/glossary/#{key}", text)


def _handle_t(pargs, kwargs, config, src_path, ix_entries, ix_counter):
    """[%t slug %] → table cross-reference (text filled in by post-processor)."""
    if not pargs:
        return _missing_shortcode_arg("t", "slug", src_path)
    return _crossref_link("tbl-ref", f"#t:{pargs[0]}")


def _handle_x(pargs, kwargs, config, src_path, ix_entries, ix_counter):
    """[%x slug %] → cross-reference to another chapter/appendix."""
    if not pargs:
        return _missing_shortcode_arg("x", "slug", src_path)
    slug = pargs[0]
    order = config.get("order", {})
    if slug not in order:
        util.warn(f"[%x%] unknown slug '{slug}' in {src_path}")
        return _crossref_link("xref", f"@/{slug}/", slug)
    entry = order[slug]
    label = "Chapter" if entry["kind"] == "lessons" else "Appendix"
    number = entry["number"]
    return _crossref_link("xref", f"@/{slug}/", f"{label} {number}")


def _handle_i(pargs, kwargs, config, src_path, ix_entries, ix_counter):
    """[%i "key" "text" %] or [%i "key" %] → index entry span."""
    if not pargs:
        return _missing_shortcode_arg("i", "key", src_path)
    key = pargs[0]
    text = pargs[1] if len(pargs) > 1 else key

    page_slug = _page_slug(src_path)
    ix_counter[0] += 1
    uid = f"ix-{page_slug}-{ix_counter[0]}"

    ix_entries.append({"key": key, "text": text, "slug": page_slug, "uid": uid})

    return f'<span class="ix-ref" data-ix-key="{key}" id="{uid}">{text}</span>'


def _handle_linecount(pargs, kwargs, config, src_path, ix_entries, ix_counter):
    """[%linecount file %] → count of non-blank lines in file."""
    if not pargs:
        return _missing_shortcode_arg("linecount", "filename", src_path, "0")
    filename = pargs[0]
    filepath = src_path.parent / filename
    try:
        lines = filepath.read_text(encoding="utf-8").splitlines()
        count = sum(1 for line in lines if line.strip())
        return str(count)
    except Exception as exc:
        util.warn(f"[%linecount%] unable to read {filepath}: {exc}")
        return "0"


def _handle_inc(pargs, kwargs, config, src_path, ix_entries, ix_counter):
    """[%inc file %] → <div data-inc="FILE"></div> with optional filters."""
    # Pattern expansion mode: pat=P fill="a b c"
    if "pat" in kwargs:
        return _handle_inc_pattern(pargs, kwargs, config, src_path, ix_entries, ix_counter)

    if not pargs:
        util.warn(f"[%inc%] shortcode missing filename in {src_path}")
        return ""

    filename = pargs[0]
    mark = kwargs.get("mark", "")
    omit = kwargs.get("omit", "")
    head = kwargs.get("head", "")
    scrub = kwargs.get("scrub", "")

    attrs = [f'data-inc="{filename}"']

    if mark:
        attrs.append(f'data-mark="{mark}"')
    if omit:
        attrs.append(f'data-omit="{omit}"')
    elif head:
        attrs.append(f'data-head="{head}"')
    if scrub:
        attrs.append(f'data-scrub="{scrub}"')

    attr_str = " ".join(attrs)
    return f"<div {attr_str}></div>"


def _handle_inc_pattern(pargs, kwargs, config, src_path, ix_entries, ix_counter):
    """Handle [%inc pat=P fill="a b …" %] wildcard expansion."""
    pat = kwargs["pat"]
    fill_str = kwargs.get("fill", "")
    fill_words = fill_str.split()

    parts = []
    for word in fill_words:
        if "*" in pat:
            filename = pat.replace("*", word)
        else:
            filename = pat

        filepath = src_path.parent / filename
        if not filepath.exists():
            util.warn(f"[%inc pat=%] file {filepath} does not exist, skipping")
            continue
        parts.append(f'<div data-inc="{filename}"></div>')

    return '\n\n<p class="continuation"></p>\n\n'.join(parts)


def _handle_figure(pargs, kwargs, config, src_path, ix_entries, ix_counter):
    """[% figure slug=S img=I alt=T caption=C %] → <figure> block."""
    slug = kwargs.get("slug", "")
    img = kwargs.get("img", "")
    alt = kwargs.get("alt", "")
    caption = kwargs.get("caption", "")

    if not slug:
        util.warn(f"[%figure%] missing slug= in {src_path}")
    if not img:
        util.warn(f"[%figure%] missing img= in {src_path}")

    return (
        f'<figure id="f:{slug}">\n'
        f'<img src="{img}" alt="{alt}"/>\n'
        f"<figcaption>{caption}</figcaption>\n"
        f"</figure>"
    )


def _handle_table(pargs, kwargs, config, src_path, ix_entries, ix_counter):
    """[% table slug=S tbl=P caption=C %] → wrapped table div."""
    slug = kwargs.get("slug", "")
    tbl = kwargs.get("tbl", "")
    caption = kwargs.get("caption", "")

    if not slug:
        util.warn(f"[%table%] missing slug= in {src_path}")
    if not tbl:
        util.warn(f"[%table%] missing tbl= in {src_path}")
        return f'<div id="t:{slug}" data-caption="{caption}" markdown="1"><!-- missing tbl --></div>'

    filepath = src_path.parent / tbl
    try:
        file_content = filepath.read_text(encoding="utf-8")
    except Exception as exc:
        util.warn(f"[%table%] unable to read {filepath}: {exc}")
        return f'<div id="t:{slug}" data-caption="{caption}" markdown="1"><!-- error reading {tbl} --></div>'

    return (
        f'<div id="t:{slug}" data-caption="{caption}" markdown="1">\n'
        f"{file_content}\n"
        f"</div>"
    )


def _handle_fixme(pargs, kwargs, config, src_path, ix_entries, ix_counter):
    """[%fixme "text" %] → visible TODO note."""
    text = pargs[0] if pargs else "FIXME"
    return f'<div class="fixme"><strong>FIXME:</strong> {text}</div>'


def _handle_issue(pargs, kwargs, config, src_path, ix_entries, ix_counter):
    """[%issue N %] → link to GitHub issue."""
    if not pargs:
        return ""
    num = pargs[0]
    repo = config.get("repo", "")
    if repo:
        return f'<a class="issue" href="{repo}/issues/{num}">issue {num}</a>'
    return f'<span class="issue">issue {num}</span>'


def _handle_thanks(pargs, kwargs, config, src_path, ix_entries, ix_counter):
    """[% thanks %] → comma-separated list of contributor names from info/thanks.yml."""
    import yaml as _yaml
    # Look for thanks.yml relative to project root (parent of src)
    root = config["src"].parent if config["src"].name != "." else config["src"]
    thanks_path = config["extras"] / "thanks.yml"
    try:
        data = _yaml.safe_load(thanks_path.read_text(encoding="utf-8")) or []
        names = []
        for person in data:
            if person.get("order", "pf") == "pf":
                names.append(f"{person['personal']} {person['family']}")
            else:
                names.append(f"{person['family']} {person['personal']}")
        return ", ".join(names)
    except Exception as exc:
        util.warn(f"[%thanks%] unable to read {thanks_path}: {exc}")
        return "the contributors"


# ---------------------------------------------------------------------------
# Handler dispatch table
# ---------------------------------------------------------------------------

_HANDLERS = {
    "g": _handle_g,
    "b": _handle_b,
    "f": _handle_f,
    "t": _handle_t,
    "x": _handle_x,
    "i": _handle_i,
    "linecount": _handle_linecount,
    "inc": _handle_inc,
    "figure": _handle_figure,
    "table": _handle_table,
    "fixme": _handle_fixme,
    "issue": _handle_issue,
    "thanks": _handle_thanks,
}

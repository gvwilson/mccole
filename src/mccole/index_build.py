"""Generate index page content from collected index entries."""

from collections import defaultdict


def build_index_page(ix_entries, config):
    """
    Generate index/index.md content from collected ix_entries.

    ix_entries: list of {"key": str, "text": str, "slug": str, "uid": str}
    config: build config dict (has config["order"] for title lookup)

    Returns a Markdown string (the content for the index page),
    or None if ix_entries is empty.
    """
    if not ix_entries:
        return None

    # Group entries by key, collecting all occurrences
    # key → {"text": str, "occurrences": [{"slug": str, "uid": str, "text": str}]}
    by_key = {}
    for entry in ix_entries:
        key = entry["key"]
        if key not in by_key:
            by_key[key] = {"text": entry["text"], "occurrences": []}
        by_key[key]["occurrences"].append(
            {"slug": entry["slug"], "uid": entry["uid"], "text": entry["text"]}
        )

    # Group keys by first letter of display text (uppercase)
    by_letter = defaultdict(list)
    for key, data in by_key.items():
        first_letter = data["text"][0].upper() if data["text"] else "#"
        by_letter[first_letter].append(key)

    # Sort: letters alphabetically, keys within each group case-insensitively
    lines = ["# Index"]

    for letter in sorted(by_letter.keys()):
        lines.append("")
        lines.append(f"## {letter}")
        lines.append("")

        keys_in_group = sorted(by_letter[letter], key=lambda k: k.lower())
        for key in keys_in_group:
            data = by_key[key]
            text = data["text"]
            links = []
            for occ in data["occurrences"]:
                slug = occ["slug"]
                uid = occ["uid"]
                occ_text = occ["text"]
                links.append(f"[{occ_text}](@/{slug}/#{uid})")
            line = f"{text}: {', '.join(links)}"
            lines.append(line)
            lines.append("")

    return "\n".join(lines)

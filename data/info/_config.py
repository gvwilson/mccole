"""Ivy configuration file."""

# ----------------------------------------

# Abbreviation for this document.
abbrev = "FIXME"

# GitHub repository.
github = "FIXME"

# Site title and subtitle.
title = "FIXME"
tagline = "FIXME"
author = "FIXME"

# Chapters.
chapters = [
    "FIXME",
]

# Appendices (slugs in order).
appendices = [
    "bibliography",
    "syllabus",
    "license",
    "conduct",
    "glossary",
    "links",
    "credits",
    "contents",
]

# Debug.
debug = False

# Warn about missing or unused entries.
warnings = False

# ----------------------------------------

# Use our own theme.
theme = "mccole"

# Enable various Markdown extensions.
markdown_settings = {
    "extensions": [
        "markdown.extensions.extra",
        "pymdownx.superfences"
    ]
}

# Links (inserted into Markdown files for consistency).
bibliography = "info/bibliography.bib"
bibliography_style = "unsrt"
glossary = "info/glossary.yml"
links = "info/links.yml"

# Language code.
lang = "en"

# Input and output directories.
src_dir = "src"
out_dir = "docs"

# Use "a/" URLs instead of "a.html".
extension = "/"

# Files to copy verbatim.
copy = [
    "*.html",
    "*.pdf",
    "*.png",
    "*.py",
    "*.svg",
]

# Exclusions (don't process).
exclude = [
    "*.csv",
    "*.gz",
    "*.out",
    "*.pdf",
    "*.png",
    "*.py",
    "*.pyc",
    "*.svg",
    "*~",
    "*/__pycache__"
]

# Display values for LaTeX generation.
if __name__ == "__main__":
    import sys
    assert len(sys.argv) == 2, "Expect exactly one argument"
    if sys.argv[1] == "--abbrev":
        print(abbrev)
    elif sys.argv[1] == "--latex":
        print(f"\\title{{{title}}}")
        print(f"\\subtitle{{{tagline}}}")
        print(f"\\author{{{author}}}")
    else:
        assert False, f"Unknown flag {sys.argv[1]}"

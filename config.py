# Tutorial information
title = "McCole Template"
repo = "https://github.com/gvwilson/mccole"
author = {
    "name": "Greg Wilson",
    "email": "gvwilson@third-bit.com",
    "site": "https://third-bit.com/",
}
lang = "en"
highlight = "tango.css"
slug = "mccole"

chapters = [
    "intro",
    "finale",
]

appendices = [
    "license",
    "conduct",
    "contrib",
    "bib",
    "glossary",
    "colophon",
    "contents",
]

# What to copy.
copy = [
    "*.svg",
]

# Files and directories to skip.
exclude = {}

# Theme information.
theme = "mccole"
src_dir = "src"
out_dir = "docs"
extension = "/"

# Enable various Markdown extensions.
markdown_settings = {
    "extensions": [
        "markdown.extensions.extra",
        "markdown.extensions.smarty",
        "pymdownx.superfences",
    ]
}

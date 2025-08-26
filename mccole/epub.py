"""Generate .epub from output HTML."""

import argparse
from pathlib import Path
from datetime import datetime

from bs4 import BeautifulSoup
from ebooklib import epub


SECTIONS = ("div#lessons", "div#appendices")

NAV_CONTENT = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>Table of Contents</title>
</head>
<body>
    <nav epub:type="toc">
        <h1>Table of Contents</h1>
        <ol>
            {nav_items}
        </ol>
    </nav>
</body>
</html>"""

XHTML_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{title}</title>
    {css_link}
</head>
<body>
<div>
{body}
</div>
</body>
</html>"""


def main(opt):
    """Generate .epub."""
    book_title, contents = _get_contents(opt)

    book = epub.EpubBook()
    book.set_identifier(opt.id)
    book.set_title(book_title)
    book.set_language("en")
    book.add_metadata("DC", "publisher", "Open Source")
    book.add_metadata("DC", "date", datetime.now().strftime("%Y-%m-%d"))
    for author in opt.authors:
        book.add_author(author)

    css_item = epub.EpubItem(
        uid="main_css",
        file_name="styles/main.css",
        media_type="text/css",
        content=opt.css.read_bytes(),
    )
    book.add_item(css_item)
    css_link = '<link rel="stylesheet" type="text/css" href="styles/main.css"/>'

    chapters = []
    spine = ["nav"]

    for i, (chapter_title, chapter_body) in enumerate(contents.items()):
        chapter = epub.EpubHtml(title=chapter_title, file_name=f"chapter_{i}.xhtml")
        chapter.content = XHTML_TEMPLATE.format(
            title=chapter_title, body=chapter_body.prettify(), css_link=css_link
        ).encode("utf-8")
        book.add_item(chapter)
        chapters.append(chapter)
        spine.append(chapter)

    book.toc = [
        (epub.Link(chap.file_name, chap.title, chap.id), []) for chap in chapters
    ]
    book.add_item(epub.EpubNcx())
    nav = epub.EpubNav()
    nav.content = NAV_CONTENT.format(
        nav_items="".join(
            f'<li><a href="{chap.file_name}">{chap.title}</a></li>' for chap in chapters
        )
    )
    book.add_item(nav)

    book.spine = spine
    epub.write_epub(opt.out, book)


def construct_parser(parser):
    """Parse command-line arguments."""
    parser.add_argument("--authors", nargs="+", help="author names")
    parser.add_argument("--css", type=Path, help="CSS file to include in EPUB")
    parser.add_argument("--id", type=str, help="book identifier")
    parser.add_argument("--out", type=Path, help="output file")
    parser.add_argument(
        "--src", type=Path, default=Path("docs"), help="input directory"
    )


def _get_contents(opt):
    """Get filepaths and titles from index.html."""
    index = opt.src / "index.html"
    doc = BeautifulSoup(index.read_text(), "html.parser")
    book_title = doc.select_one("h1").get_text().strip()
    contents = {}
    for selector in SECTIONS:
        div = doc.select_one(selector)
        assert div is not None, f"{index} does not contain {selector}"
        for entry in div.select("li>a[href]"):
            chapter_title = entry.get_text().strip()
            sub_path = opt.src / entry["href"] / "index.html"
            sub_doc = BeautifulSoup(sub_path.read_text(), "html.parser").select_one(
                "main"
            )
            assert sub_doc is not None, f"{sub_path} does not contain main section"
            assert sub_doc.get_text().strip(), f"{sub_path} main section is empty"
            contents[chapter_title] = sub_doc
    return book_title, contents

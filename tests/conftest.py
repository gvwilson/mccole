"""Shared fixtures for mccole tests."""

from pathlib import Path
import textwrap

import pytest

from mccole import util


@pytest.fixture
def src_dir(tmp_path):
    """Create a minimal source tree with README.md and links."""
    src = tmp_path / "src"
    src.mkdir()
    # Create a minimal README with one lesson and one appendix
    readme = textwrap.dedent("""\
    # Test Book

    <div id="lessons" markdown="1">
    -   [Intro](@/intro/)
    </div>

    <div id="appendices" markdown="1">
    -   [Refs](@/refs/)
    </div>
    """)
    (src / "README.md").write_text(readme, encoding="utf-8")
    # Create intro lesson
    (src / "intro").mkdir()
    (src / "intro" / "index.md").write_text(
        "# Intro\n\nHello, world.\n", encoding="utf-8"
    )
    # Create refs appendix
    (src / "refs").mkdir()
    (src / "refs" / "index.md").write_text(
        "# Refs\n\nSee appendix.\n", encoding="utf-8"
    )
    # Create link definitions
    (src / "_extras").mkdir()
    (src / "_extras" / "links.md").write_text(
        "[link]: https://example.com\n", encoding="utf-8"
    )
    return src


@pytest.fixture
def src_with_glossary_bib(tmp_path):
    """Create a source tree with glossary and bibliography."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "README.md").write_text(
        textwrap.dedent("""\
    # Test Book

    <div id="lessons" markdown="1">
    -   [Lesson One](@/lesson1/)
    </div>

    <div id="appendices" markdown="1">
    </div>
    """),
        encoding="utf-8",
    )
    (src / "lesson1").mkdir()
    (src / "lesson1" / "index.md").write_text(
        '# Lesson\n\nSee [%g term1 "the term" %] and [%b Key2020 %].\n',
        encoding="utf-8",
    )
    (src / "_extras").mkdir()
    (src / "_extras" / "links.md").write_text("", encoding="utf-8")
    (src / "glossary").mkdir()
    (src / "glossary" / "index.md").write_text(
        textwrap.dedent("""\
    <span id="term1">glossary term</span>
    :   A definition.
    """),
        encoding="utf-8",
    )
    (src / "bibliography").mkdir()
    (src / "bibliography" / "index.md").write_text(
        textwrap.dedent("""\
    <span id="Key2020">Key2020</span>
    :   Author.
        Title.
        Publisher,
        2020,
        ISBN.
    """),
        encoding="utf-8",
    )
    return src


@pytest.fixture
def basic_config(src_dir):
    """Return a basic build config dict."""
    return {
        "src": src_dir,
        "dst": src_dir.parent / "docs",
        "home_page": Path("README.md"),
        "links": util.load_links(src_dir),
        "order": util.load_order(src_dir, Path("README.md")),
        "templates": src_dir.parent / "_templates",
        "repo": "https://github.com/test/repo",
        "extras": src_dir / "_extras",
        "lang": "en",
        "math": False,
        "forma": False,
        "extra_html": "",
    }

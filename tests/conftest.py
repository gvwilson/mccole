"""Test configuration and fixtures."""

import argparse

from bs4 import BeautifulSoup
import pytest

CONFIG = """\
[tool.mccole]
skips = []
"""

GLOSSARY = """
# Glossary
<span id="first">first term</span>
:   body
<span id="second">second term</span>
:   body
"""

README = """
# Tutorial

<div id="lessons" markdown="1"></div>
<div id="appendices" markdown="1">

1.  [Glossary](./glossary/)

</div>
"""

TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
  <head>
    <title></title>
  </head>
  <body>
    <nav>
      <span id="nav-lessons" class="dropdown-content">
{% for key in lessons %}<a href="{{key}}">{{lessons[key]}}</a>{% endfor %}
      </span>
      <span id="nav-extras" class="dropdown-content">
{% for key in appendices %}<a href="{{key}}">{{appendices[key]}}</a>{% endfor %}
      </span>
    </nav>
    <main>
{{content}}
    </main>
  </body>
</html>
"""


def make_fs(spec):
    """Build a directory tree and populate files."""
    for filepath, content in spec.items():
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content)


def read_doc(filepath):
    """Read HTML as DOM."""
    return BeautifulSoup(filepath.read_text(), "html.parser")


@pytest.fixture
def bare_fs(tmp_path):
    make_fs(
        {
            tmp_path / "README.md": README,
            tmp_path / "templates" / "page.html": TEMPLATE,
            tmp_path / "pyproject.toml": CONFIG,
            tmp_path / "glossary" / "index.md": GLOSSARY,
        }
    )
    return tmp_path


@pytest.fixture
def build_opt(bare_fs):
    return argparse.Namespace(
        config=bare_fs / "pyproject.toml",
        dst=bare_fs / "docs",
        links=None,
        src=bare_fs,
        templates=bare_fs / "templates",
    )


@pytest.fixture
def glossary_dst_dir(bare_fs, build_opt):
    """Path to glossary output directory."""
    return bare_fs / build_opt.dst / "glossary"


@pytest.fixture
def glossary_dst_file(glossary_dst_dir):
    """Path to glossary output file."""
    return glossary_dst_dir / "index.html"


@pytest.fixture
def glossary_src_file(bare_fs, build_opt):
    """Path to glossary source file."""
    return bare_fs / build_opt.src / "glossary" / "index.md"


@pytest.fixture
def readme_dst_file(build_opt):
    """Path to output index.html file constructed from README.md"""
    return build_opt.dst / "index.html"


@pytest.fixture
def minimal_dst_top_level(glossary_dst_dir, readme_dst_file):
    """Minimal expected contents of output directory."""
    return {glossary_dst_dir, readme_dst_file}


@pytest.fixture
def lint_opt(build_opt):
    return argparse.Namespace(
        dst=build_opt.dst,
        src=build_opt.src,
        html=False,
        links=None,
    )

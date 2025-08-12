"""Test configuration and fixtures."""

import argparse

import pytest

CONFIG = """\
[tool.mccole]
skips = []
"""

GLOSSARY = """`
# Glossary
<span id="first">first term</span>
:   body
<span id="second">second term</span>
:   body
"""

TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
  <head>
    <title></title>
  </head>
  <body>
    <nav>
      <span id="nav-lessons" class="dropdown-content"></span>
      <span id="nav-extras" class="dropdown-content"></span>
    </nav>
    <main>
{{content}}
    </main>
  </body>
</html>
"""


@pytest.fixture
def bare_fs(tmp_path):
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "page.html").write_text(TEMPLATE)

    (tmp_path / "pyproject.toml").write_text(CONFIG)

    (tmp_path / "glossary").mkdir()
    (tmp_path / "glossary" / "index.md").write_text(GLOSSARY)

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
def glossary_dst(glossary_dst_dir):
    """Path to glossary output file."""
    return glossary_dst_dir / "index.html"


@pytest.fixture
def glossary_src(bare_fs, build_opt):
    """Path to glossary source file."""
    return bare_fs / build_opt.src / "glossary" / "index.md"


@pytest.fixture
def lint_opt(build_opt):
    return argparse.Namespace(
        dst=build_opt.dst,
        html=False,
    )

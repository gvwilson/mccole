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
<html>
  <head>
    <title></title>
  </head>
  <body>
{{content}}
  </body>
</html>
"""


@pytest.fixture
def bare_fs(tmp_path):
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "page.html").write_text(TEMPLATE)
    (tmp_path / "pyproject.toml").write_text(CONFIG)
    return tmp_path


@pytest.fixture
def build_opt(bare_fs):
    return argparse.Namespace(
        config=bare_fs / "pyproject.toml",
        dst=bare_fs / "docs",
        src=bare_fs,
        templates=bare_fs / "templates",
    )


@pytest.fixture
def glossary_path(bare_fs, build_opt):
    """Create glossary file and return its path."""
    glossary_path = bare_fs / build_opt.src / "glossary" / "index.md"
    glossary_path.parent.mkdir()
    glossary_path.write_text(GLOSSARY)
    return glossary_path


@pytest.fixture
def lint_opt(build_opt):
    return argparse.Namespace(
        dst=build_opt.dst,
    )

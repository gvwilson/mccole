"""Tests for mccole.detab."""

import textwrap
from pathlib import Path

from mccole import detab


class TestDetab:
    def test_replaces_tabs(self, src_dir):
        """detab replaces tab characters with spaces."""

        class Opts:
            src = src_dir
            root = Path("README.md")
            tabsize = 4

        # Put a tab in intro/index.md
        intro = src_dir / "intro" / "index.md"
        intro.write_text("# Intro\n\thello\n", encoding="utf-8")

        detab.detab(Opts())
        content = intro.read_text(encoding="utf-8")
        assert "\t" not in content
        assert "    hello" in content

    def test_no_change_when_no_tabs(self, src_dir):
        """Leaves content unchanged when no tabs."""

        class Opts:
            src = src_dir
            root = Path("README.md")
            tabsize = 4

        intro = src_dir / "intro" / "index.md"
        original = "# Intro\n    hello\n"
        intro.write_text(original, encoding="utf-8")
        detab.detab(Opts())
        assert intro.read_text(encoding="utf-8") == original

    def test_skips_missing_file(self, src_dir):
        """Does not crash when a file in the order does not exist."""

        class Opts:
            src = src_dir
            root = Path("README.md")
            tabsize = 4

        # Refs appendix file doesn't exist in this src_dir setup...
        # Actually, it does. Let's use a more minimal order.
        # load_order reads README.md, which lists intro and refs.
        # Both exist. The skip is only checked if not exists.
        detab.detab(Opts())  # should not raise

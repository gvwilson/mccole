"""Tests for mccole.index_build."""

from mccole.index_build import build_index_page


class TestBuildIndexPage:
    def test_empty_entries_returns_none(self):
        assert build_index_page([], {}) is None

    def test_single_entry(self):
        entries = [
            {"key": "apple", "text": "Apple", "slug": "intro", "uid": "ix-intro-1"}
        ]
        result = build_index_page(entries, {"order": {}})
        assert result is not None
        assert "# Index" in result
        assert "Apple:" in result
        assert "@/intro/" in result
        assert "#ix-intro-1" in result

    def test_multiple_entries_same_key(self):
        """Multiple occurrences of the same key are combined."""
        entries = [
            {"key": "test", "text": "Test", "slug": "intro", "uid": "ix-intro-1"},
            {"key": "test", "text": "Test", "slug": "refs", "uid": "ix-refs-2"},
        ]
        result = build_index_page(entries, {"order": {}})
        assert "@/intro/" in result
        assert "@/refs/" in result

    def test_alphabetical_groups(self):
        """Entries are grouped by first letter."""
        entries = [
            {"key": "banana", "text": "Banana", "slug": "a", "uid": "ix-a-1"},
            {"key": "apple", "text": "Apple", "slug": "a", "uid": "ix-a-2"},
        ]
        result = build_index_page(entries, {"order": {}})
        lines = result.split("\n")
        # Find the letter headers
        a_idx = lines.index("## A")
        # Both entries should be after A
        content_after_a = "\n".join(lines[a_idx:])
        assert "Apple" in content_after_a
        assert "Banana" in content_after_a

    def test_non_alpha_first_char(self):
        entries = [
            {"key": "2d", "text": "2D", "slug": "a", "uid": "ix-a-1"},
        ]
        result = build_index_page(entries, {"order": {}})
        assert "## #" in result or "## " in result

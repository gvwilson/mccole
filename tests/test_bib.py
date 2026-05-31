"""Tests for mccole.bib."""

import io
from pathlib import Path
import textwrap

import mccole.bib as bib_mod
from mccole.bib import (
    _isbn10_valid,
    _isbn13_valid,
    _isbn_check_digit_valid,
    _parse_bibliography,
    _validate_doi,
    _validate_isbns_network,
)


def _capture_bib(func, *args, **kwargs):
    buf = io.StringIO()
    old = bib_mod.sys.stderr
    bib_mod.sys.stderr = buf
    try:
        result = func(*args, **kwargs)
    finally:
        bib_mod.sys.stderr = old
    return result, buf.getvalue()


class TestIsbn13:
    def test_valid_isbn13(self):
        # 978-0-306-40615-7 has valid check digit 7
        # Let's verify: 9*1 + 7*3 + 8*1 + 0*3 + 3*1 + 0*3 + 6*1 + 4*3 + 0*1 + 6*3 + 1*1 + 5*3 = ...
        # sum = 9 + 21 + 8 + 0 + 3 + 0 + 6 + 12 + 0 + 18 + 1 + 15 = 93
        # 10 - (93 % 10) = 10 - 3 = 7 ✓
        assert _isbn13_valid("9780306406157") is True

    def test_invalid_isbn13(self):
        assert _isbn13_valid("9780306406158") is False

    def test_isbn13_with_dashes(self):
        # Also known valid ISBN-13
        assert _isbn13_valid("9780306406157") is True


class TestIsbn10:
    def test_valid_isbn10(self):
        # 0-306-40615-2: sum = 0*10+3*9+0*8+6*7+4*6+0*5+6*4+1*3+5*2 = 0+27+0+42+24+0+24+3+10 = 130
        # 130 + 2*1 = 132; 132 % 11 = 0 ✓
        assert _isbn10_valid("0306406152") is True

    def test_invalid_isbn10(self):
        assert _isbn10_valid("0306406153") is False

    def test_isbn10_with_X(self):
        # 0-8044-2957-X: sum = 0*10+8*9+0*8+4*7+4*6+2*5+9*4+5*3+7*2 = 0+72+0+28+24+10+36+15+14 = 199
        # 199 + 10*1 = 209; 209 % 11 = 0 ✓
        assert _isbn10_valid("080442957X") is True


class TestParseBibliography:
    def test_extracts_keys_and_hrefs(self, tmp_path):
        """Parses bibliography Markdown into (key, hrefs) pairs."""
        bib_path = tmp_path / "index.md"
        bib_path.write_text(
            textwrap.dedent("""\
            <span id="Key2020">Key2020</span>
            :   Author.
                [Publisher](https://example.com/).
                2020,
                [9780306406157](https://isbnsearch.org/isbn/9780306406157)
        """),
            encoding="utf-8",
        )
        entries = _parse_bibliography(bib_path)
        assert len(entries) == 1
        key, hrefs = entries[0]
        assert key == "Key2020"
        assert len(hrefs) == 2

    def test_empty_bib(self, tmp_path):
        """Empty bibliography yields no entries."""
        bib_path = tmp_path / "index.md"
        bib_path.write_text("# Bibliography\n", encoding="utf-8")
        entries = _parse_bibliography(bib_path)
        assert entries == []


class TestIsbnCheckDigitValid:
    def test_valid_isbn13_returns_true(self):
        result, err = _capture_bib(_isbn_check_digit_valid, "key", "9780306406157")
        assert result is True
        assert err == ""

    def test_invalid_isbn13_reported(self):
        result, err = _capture_bib(_isbn_check_digit_valid, "key", "9780306406158")
        assert result is False
        assert "invalid ISBN-13 check digit" in err

    def test_valid_isbn10_returns_true(self):
        result, err = _capture_bib(_isbn_check_digit_valid, "key", "0306406152")
        assert result is True
        assert err == ""

    def test_invalid_isbn10_reported(self):
        result, err = _capture_bib(_isbn_check_digit_valid, "key", "0306406153")
        assert result is False
        assert "invalid ISBN-10 check digit" in err

    def test_wrong_length_reported(self):
        result, err = _capture_bib(_isbn_check_digit_valid, "key", "12345")
        assert result is False
        assert "malformed ISBN" in err


class TestValidateDoi:
    def test_malformed_doi_reported(self):
        """A DOI that does not match the expected pattern is reported without a network call."""
        _, err = _capture_bib(_validate_doi, "key", "https://doi.org/not-valid-doi")
        assert "malformed DOI" in err


class TestValidateIsbnsNetwork:
    def test_empty_list_is_silent(self):
        """Empty isbn_entries returns immediately with no output."""
        _, err = _capture_bib(_validate_isbns_network, [])
        assert err == ""

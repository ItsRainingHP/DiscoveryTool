from __future__ import annotations

from pathlib import Path

import pytest

from app.services.privilege_converter import (
    ConversionError,
    convert_csv_bytes,
    friendly_reason_label,
    is_truthy,
    normalize_bates_token,
    render_privilege_value,
    render_row_bates_context,
    resolve_headers,
)


def test_convert_csv_bytes_builds_privilege_rows_and_csv_text() -> None:
    csv_text = """Begin Bates num from 2026-03-20 Production,End Bates num from 2026-03-20 Production,Document Date,File Name,Email Subject,Email From,Email To,Email CC,Email BCC,Tag: Privilege - Redact,Tag: Privilege - Withhold,Tag: AC-WP,Tag: FERPA
EXAMPLE003824,EXAMPLE003825,1/24/2025,alpha.msg,Alpha Subject,Author One,To One,CC One,BCC One,TRUE,,TRUE,TRUE
"""
    result = convert_csv_bytes("sample.csv", csv_text.encode("utf-8"))

    assert result.headers == [
        "Beginning No.",
        "End No.",
        "Date",
        "Description",
        "Author",
        "Recipient(s)",
        "Privilege",
    ]
    assert result.rows == [
        [
            "EXAMPLE_003824",
            "EXAMPLE_003825",
            "1/24/2025",
            "Alpha Subject",
            "Author One",
            "To One; CC One; BCC One",
            "Redacted - Attorney Client Privilege; FERPA",
        ]
    ]
    assert (
        result.csvText
        == "Beginning No.,End No.,Date,Description,Author,Recipient(s),Privilege\r\n"
        "EXAMPLE_003824,EXAMPLE_003825,1/24/2025,Alpha Subject,Author One,To One; CC One; BCC One,Redacted - Attorney Client Privilege; FERPA\r\n"
    )
    assert result.stats.total_rows == 1
    assert result.stats.exported_rows == 1
    assert result.stats.reason_columns == 2


def test_convert_csv_bytes_falls_back_to_file_name_and_preserves_blanks() -> None:
    csv_text = """Begin Bates num from 2026-03-20 Production,End Bates num from 2026-03-20 Production,Document Date,File Name,Email Subject,Email From,Email To,Email CC,Email BCC,Tag: Privilege - Redact,Tag: Privilege - Withhold,Tag: Employee Privacy
EXAMPLE004153,EXAMPLE004153,,ET1-10photo1.png,,,,,,TRUE,,TRUE
"""
    result = convert_csv_bytes("sample.csv", csv_text.encode("utf-8"))

    assert result.rows == [
        [
            "EXAMPLE_004153",
            "EXAMPLE_004153",
            "",
            "ET1-10photo1.png",
            "",
            "",
            "Redacted - Employee Privacy",
        ]
    ]


def test_convert_csv_bytes_supports_withheld_rows() -> None:
    csv_text = """Begin Bates num from 2026-03-20 Production,End Bates num from 2026-03-20 Production,Document Date,File Name,Email Subject,Email From,Email To,Email CC,Email BCC,Tag: Privilege - Redact,Tag: Privilege - Withhold,Tag: FERPA,Tag: PID
EXAMPLE004000,EXAMPLE004001,4/1/2026,withheld.msg,,Author Two,To Two,,, ,TRUE,TRUE,TRUE
"""
    result = convert_csv_bytes("sample.csv", csv_text.encode("utf-8"))

    assert result.rows[0][6] == "Withheld - FERPA; PID"


def test_convert_csv_bytes_raises_for_missing_required_headers() -> None:
    csv_text = "Document Date,File Name\n1/24/2025,alpha.msg\n"

    with pytest.raises(ConversionError, match="missing the required column"):
        convert_csv_bytes("sample.csv", csv_text.encode("utf-8"))


def test_convert_csv_bytes_raises_for_ambiguous_status_flags() -> None:
    csv_text = """Begin Bates num from 2026-03-20 Production,End Bates num from 2026-03-20 Production,Document Date,File Name,Email Subject,Email From,Email To,Email CC,Email BCC,Tag: Privilege - Redact,Tag: Privilege - Withhold,Tag: AC-WP
EXAMPLE003824,EXAMPLE003825,1/24/2025,alpha.msg,Alpha Subject,Author One,To One,,,TRUE,TRUE,TRUE
"""

    with pytest.raises(ConversionError, match="must have exactly one"):
        convert_csv_bytes("sample.csv", csv_text.encode("utf-8"))


def test_convert_csv_bytes_raises_for_missing_reason() -> None:
    csv_text = """Begin Bates num from 2026-03-20 Production,End Bates num from 2026-03-20 Production,Document Date,File Name,Email Subject,Email From,Email To,Email CC,Email BCC,Tag: Privilege - Redact,Tag: Privilege - Withhold,Tag: AC-WP
EXAMPLE003824,EXAMPLE003825,1/24/2025,alpha.msg,Alpha Subject,Author One,To One,,,TRUE,,
"""

    with pytest.raises(
        ConversionError,
        match=r"Row 2 \[EXAMPLE003824\]-\[EXAMPLE003825\] must include at least one privilege reason marked TRUE\.",
    ):
        convert_csv_bytes("sample.csv", csv_text.encode("utf-8"))


def test_convert_csv_bytes_warns_for_unparseable_bates_values() -> None:
    csv_text = """Begin Bates num from 2026-03-20 Production,End Bates num from 2026-03-20 Production,Document Date,File Name,Email Subject,Email From,Email To,Email CC,Email BCC,Tag: Privilege - Redact,Tag: Privilege - Withhold,Tag: AC-WP
BADVALUE,EXAMPLE003825,1/24/2025,alpha.msg,Alpha Subject,Author One,To One,,,TRUE,,TRUE
"""
    result = convert_csv_bytes("sample.csv", csv_text.encode("utf-8"))

    assert result.rows[0][0] == "BADVALUE"
    assert result.warnings == ["Row 2 Beginning Bates value 'BADVALUE' could not be normalized."]


@pytest.mark.parametrize(
    "value,expected",
    [
        ("TRUE", True),
        ("true", True),
        (" True ", True),
        ("FALSE", False),
        ("", False),
        (None, False),
        ("yes", False),
        ("1", False),
    ],
)
def test_is_truthy(value: str | None, expected: bool) -> None:
    assert is_truthy(value) is expected


@pytest.mark.parametrize(
    "header,expected",
    [
        ("Tag: AC-WP", "Attorney Client Privilege"),
        ("Tag: FERPA", "FERPA"),
        ("  Tag: PID  ", "PID"),
        ("PlainLabel", "PlainLabel"),
        ("AC-WP", "Attorney Client Privilege"),
    ],
)
def test_friendly_reason_label_resolves_known_and_unknown(header: str, expected: str) -> None:
    assert friendly_reason_label(header) == expected


def test_normalize_bates_token_inserts_underscore_when_missing() -> None:
    warnings: list[str] = []
    assert (
        normalize_bates_token("EXAMPLE003824", row_number=2, column_label="Beginning", warnings=warnings)
        == "EXAMPLE_003824"
    )
    assert warnings == []


def test_normalize_bates_token_preserves_existing_underscore() -> None:
    warnings: list[str] = []
    assert (
        normalize_bates_token("EXAMPLE_003824", row_number=2, column_label="Beginning", warnings=warnings)
        == "EXAMPLE_003824"
    )
    assert warnings == []


def test_normalize_bates_token_warns_on_blank() -> None:
    warnings: list[str] = []
    assert (
        normalize_bates_token("   ", row_number=4, column_label="End", warnings=warnings) == ""
    )
    assert warnings == ["Row 4 End Bates value is blank and was left unchanged."]


def test_normalize_bates_token_warns_on_no_trailing_digits() -> None:
    warnings: list[str] = []
    result = normalize_bates_token(
        "NODIGITS", row_number=5, column_label="Beginning", warnings=warnings
    )
    assert result == "NODIGITS"
    assert warnings == ["Row 5 Beginning Bates value 'NODIGITS' could not be normalized."]


def test_render_privilege_value_joins_friendly_reason_labels() -> None:
    rendered = render_privilege_value(
        "Withheld", ["Tag: AC-WP", "Tag: FERPA", "Tag: PID"]
    )
    assert rendered == "Withheld - Attorney Client Privilege; FERPA; PID"


def test_render_row_bates_context_falls_back_to_blank_marker() -> None:
    headers = {"begin": "Begin Col", "end": "End Col"}
    row = {"Begin Col": "  ", "End Col": "EXAMPLE_000001"}
    assert (
        render_row_bates_context(row, headers, row_number=12)
        == "Row 12 [<blank>]-[EXAMPLE_000001]"
    )


def test_resolve_headers_rejects_empty_fieldnames() -> None:
    with pytest.raises(ConversionError, match="empty"):
        resolve_headers([])


def test_resolve_headers_rejects_missing_reason_columns_after_withhold() -> None:
    fieldnames = [
        "Begin Bates num from 2026-03-20 Production",
        "End Bates num from 2026-03-20 Production",
        "Document Date",
        "File Name",
        "Email Subject",
        "Email From",
        "Email To",
        "Email CC",
        "Email BCC",
        "Tag: Privilege - Redact",
        "Tag: Privilege - Withhold",
    ]

    with pytest.raises(ConversionError, match="at least one privilege reason column"):
        resolve_headers(fieldnames)


def test_convert_csv_bytes_skips_completely_blank_rows() -> None:
    csv_text = """Begin Bates num from 2026-03-20 Production,End Bates num from 2026-03-20 Production,Document Date,File Name,Email Subject,Email From,Email To,Email CC,Email BCC,Tag: Privilege - Redact,Tag: Privilege - Withhold,Tag: AC-WP
,,,,,,,,,,,
EXAMPLE003824,EXAMPLE003825,1/24/2025,alpha.msg,Alpha Subject,Author One,To One,,,TRUE,,TRUE
"""
    result = convert_csv_bytes("sample.csv", csv_text.encode("utf-8"))

    assert result.stats.total_rows == 1
    assert result.stats.exported_rows == 1


def test_convert_csv_bytes_rejects_when_neither_status_flag_set() -> None:
    csv_text = """Begin Bates num from 2026-03-20 Production,End Bates num from 2026-03-20 Production,Document Date,File Name,Email Subject,Email From,Email To,Email CC,Email BCC,Tag: Privilege - Redact,Tag: Privilege - Withhold,Tag: AC-WP
EXAMPLE003824,EXAMPLE003825,1/24/2025,alpha.msg,Alpha Subject,Author One,To One,,,,,TRUE
"""

    with pytest.raises(ConversionError, match="must have exactly one"):
        convert_csv_bytes("sample.csv", csv_text.encode("utf-8"))


def test_convert_csv_bytes_uses_default_filename_when_blank() -> None:
    csv_text = """Begin Bates num from 2026-03-20 Production,End Bates num from 2026-03-20 Production,Document Date,File Name,Email Subject,Email From,Email To,Email CC,Email BCC,Tag: Privilege - Redact,Tag: Privilege - Withhold,Tag: AC-WP
EXAMPLE003824,EXAMPLE003825,1/24/2025,alpha.msg,Alpha Subject,Author One,To One,,,TRUE,,TRUE
"""
    result = convert_csv_bytes("", csv_text.encode("utf-8"))

    assert result.sourceFilename == "uploaded.csv"
    assert result.downloadFilename == "converted-privilege-log.csv"


def test_convert_csv_bytes_csv_text_quotes_values_with_commas() -> None:
    csv_text = """Begin Bates num from 2026-03-20 Production,End Bates num from 2026-03-20 Production,Document Date,File Name,Email Subject,Email From,Email To,Email CC,Email BCC,Tag: Privilege - Redact,Tag: Privilege - Withhold,Tag: AC-WP
EXAMPLE003824,EXAMPLE003825,1/24/2025,alpha.msg,"Subject, with comma",Author One,To One,,,TRUE,,TRUE
"""
    result = convert_csv_bytes("sample.csv", csv_text.encode("utf-8"))

    # csv.writer must quote the field that contains a comma so downstream parsers can read it.
    assert '"Subject, with comma"' in result.csvText


def test_example_privilege_csv_integration() -> None:
    example_path = Path(__file__).resolve().parents[2] / "examples" / "privilege" / "example.csv"
    result = convert_csv_bytes(example_path.name, example_path.read_bytes())

    assert result.downloadFilename == "example-privilege-log.csv"
    assert result.stats.model_dump() == {
        "total_rows": 67,
        "exported_rows": 67,
        "reason_columns": 7,
    }
    assert result.warnings == []
    assert result.rows[0] == [
        "EXAMPLE_003824",
        "EXAMPLE_003825",
        "1/24/2025",
        'Example Thread - Family Update "Fw: About Site Visit"',
        "Owen Harper",
        "Nora Patel; Priya Nand; Lucas Reed; Maya Brooks; Ethan Park",
        "Redacted - Attorney Client Privilege; Social Security Number",
    ]
    assert result.rows[47] == [
        "EXAMPLE_004152",
        "EXAMPLE_004152",
        "10/22/2025",
        "Untitled note.msg",
        "",
        "Harper Lane; Priya Nand; Naomi Ellis; Miles Turner",
        "Withheld - FERPA; Computer Security Password",
    ]
    assert result.rows[48] == [
        "EXAMPLE_004153",
        "EXAMPLE_004153",
        "",
        "routing-note-photo-1.png",
        "",
        "",
        "Redacted - Attorney Client Privilege; FERPA",
    ]

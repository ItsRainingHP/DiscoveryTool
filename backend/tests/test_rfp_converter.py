from __future__ import annotations

from pathlib import Path

import pytest

from app.services.rfp_converter import (
    ConversionError,
    BatesInterval,
    build_section_text,
    convert_csv_bytes,
    extract_tag_label,
    merge_intervals,
    natural_language_join,
    parse_bates_value,
    render_interval,
)


def test_extract_tag_label_supports_rfp_and_rog() -> None:
    assert extract_tag_label("Tag: RFP 01") == "RFP 01"
    assert extract_tag_label("misc ROG 2 data") == "ROG 2"
    assert extract_tag_label("Tag: rfp 12") == "RFP 12"
    assert extract_tag_label("Tag: Other 12") is None


def test_parse_bates_value_requires_suffix_number() -> None:
    parsed = parse_bates_value("EXAMPLE_004203")
    assert parsed.prefix == "EXAMPLE"
    assert parsed.number == 4203
    assert parsed.width == 6

    with pytest.raises(ConversionError):
        parse_bates_value("EXAMPLE")


def test_merge_intervals_combines_contiguous_and_overlapping_ranges() -> None:
    merged = merge_intervals(
        [
            BatesInterval("EXAMPLE", 4558, 4560, "EXAMPLE_004558", 6),
            BatesInterval("EXAMPLE", 4561, 4561, "EXAMPLE_004561", 6),
            BatesInterval("EXAMPLE", 4610, 4611, "EXAMPLE_004610", 6),
            BatesInterval("EXAMPLE", 4611, 4614, "EXAMPLE_004611", 6),
        ]
    )

    assert [render_interval(interval) for interval in merged] == [
        "EXAMPLE_004558-4561",
        "EXAMPLE_004610-4614",
    ]


def test_build_section_text_renders_empty_and_natural_lists() -> None:
    assert build_section_text("RFP 02", []) == "RFP 02:\nNo responsive documents."
    assert natural_language_join(["A"]) == "A"
    assert natural_language_join(["A", "B"]) == "A and B"
    assert natural_language_join(["A", "B", "C"]) == "A, B, and C"


def test_convert_csv_bytes_skips_bad_rows_and_preserves_all_sections() -> None:
    csv_text = """Begin,End,Tag: RFP 01,Tag: ROG 02,Tag: RFP 03
EXAMPLE_004558,EXAMPLE_004560,TRUE,,
EXAMPLE_004561,EXAMPLE_004561,TRUE,TRUE,
EXAMPLE_004610,EXAMPLE_004611,TRUE,,
EXAMPLE_004613,EXAMPLE_004614,TRUE,,
EXAMPLE_004653,EXAMPLE_004704,TRUE,,
EXAMPLE_004700,BADVALUE,,TRUE,
EXAMPLE_004203,EXAMPLE_004203,,,TRUE
"""
    result = convert_csv_bytes("sample.csv", csv_text.encode("utf-8"))

    assert result.downloadFilename == "sample.txt"
    assert result.warnings == ["Row 7 skipped: Invalid Bates token: 'BADVALUE'."]
    assert [section.label for section in result.sections] == ["RFP 01", "ROG 02", "RFP 03"]
    assert result.sections[0].text == (
        "RFP 01:\nEXAMPLE_004558-4561, EXAMPLE_004610-4611, EXAMPLE_004613-4614, and EXAMPLE_004653-4704"
    )
    assert result.sections[1].text == "ROG 02:\nEXAMPLE_004561"
    assert result.sections[2].text == "RFP 03:\nEXAMPLE_004203"
    assert result.documentTextWithoutEmpty.startswith("RFP 01:\nEXAMPLE_004558-4561")
    assert result.stats.total_rows == 7
    assert result.stats.skipped_rows == 1
    assert result.stats.total_sections == 3
    assert result.stats.responsive_sections == 3


def test_convert_csv_bytes_renders_empty_sections_when_no_rows_match() -> None:
    csv_text = """Begin,End,Tag: RFP 01,Tag: RFP 02
EXAMPLE_000001,EXAMPLE_000001,TRUE,
"""
    result = convert_csv_bytes("sample.csv", csv_text.encode("utf-8"))

    assert result.sections[1].text == "RFP 02:\nNo responsive documents."
    assert "RFP 02:\nNo responsive documents." in result.documentTextWithEmpty
    assert "RFP 02:\nNo responsive documents." not in result.documentTextWithoutEmpty


def test_example_csv_integration_example2() -> None:
    example_path = Path(__file__).resolve().parents[2] / "examples" / "rfp" / "example2.csv"
    result = convert_csv_bytes(example_path.name, example_path.read_bytes())

    assert [section.label for section in result.sections] == [
        "RFP 01",
        "RFP 08",
        "RFP 14",
        "RFP 22",
        "RFP 24",
        "RFP 32",
    ]
    assert result.sections[0].text == "RFP 01:\nEXAMPLE_002762-2769"
    assert result.sections[4].text == "RFP 24:\nEXAMPLE_002904-2950"
    assert result.sections[5].text == "RFP 32:\nEXAMPLE_002951-3791"
    assert result.stats.total_rows == 81

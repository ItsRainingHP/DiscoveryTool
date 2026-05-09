from __future__ import annotations

from pathlib import Path

import pytest

from app.services.rfp_converter import (
    ConversionError,
    BatesInterval,
    build_section_text,
    convert_csv_bytes,
    decode_csv_bytes,
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


def test_extract_tag_label_returns_none_for_unrelated_headers() -> None:
    assert extract_tag_label("Begin") is None
    assert extract_tag_label("") is None
    assert extract_tag_label("Tag: Privilege - Redact") is None


def test_parse_bates_value_strips_whitespace() -> None:
    parsed = parse_bates_value("  EXAMPLE_000007  ")
    assert parsed.token == "EXAMPLE_000007"
    assert parsed.prefix == "EXAMPLE"
    assert parsed.number == 7
    assert parsed.width == 6


def test_parse_bates_value_rejects_blank() -> None:
    with pytest.raises(ConversionError):
        parse_bates_value("")


def test_render_interval_returns_token_for_single_document() -> None:
    interval = BatesInterval("EXAMPLE", 4561, 4561, "EXAMPLE_004561", 6)
    assert render_interval(interval) == "EXAMPLE_004561"


def test_render_interval_truncates_end_to_last_four_digits_for_wide_widths() -> None:
    # The renderer keeps at most the last 4 digits of the end number when the source width is >= 4.
    interval = BatesInterval("EXAMPLE", 4558, 4561, "EXAMPLE_004558", 6)
    assert render_interval(interval) == "EXAMPLE_004558-4561"


def test_render_interval_pads_short_widths() -> None:
    interval = BatesInterval("EX", 1, 9, "EX_1", 1)
    assert render_interval(interval) == "EX_1-9"

    interval_two_wide = BatesInterval("EX", 1, 12, "EX_01", 2)
    assert render_interval(interval_two_wide) == "EX_01-12"


def test_merge_intervals_handles_empty_and_singleton() -> None:
    assert merge_intervals([]) == []

    only = BatesInterval("EXAMPLE", 1, 5, "EXAMPLE_000001", 6)
    merged = merge_intervals([only])
    assert len(merged) == 1
    assert merged[0].start_number == 1
    assert merged[0].end_number == 5


def test_merge_intervals_does_not_merge_across_prefixes_or_gaps() -> None:
    intervals = [
        BatesInterval("AAA", 1, 5, "AAA_000001", 6),
        BatesInterval("BBB", 6, 7, "BBB_000006", 6),
        BatesInterval("AAA", 10, 12, "AAA_000010", 6),
    ]
    merged = merge_intervals(intervals)
    rendered = [render_interval(interval) for interval in merged]
    assert rendered == ["AAA_000001-0005", "AAA_000010-0012", "BBB_000006-0007"]


def test_merge_intervals_swallows_subsumed_ranges() -> None:
    # If a later interval is fully contained within the current merged interval, the merged
    # end number must not regress.
    intervals = [
        BatesInterval("EX", 1, 10, "EX_000001", 6),
        BatesInterval("EX", 3, 5, "EX_000003", 6),
    ]
    merged = merge_intervals(intervals)
    assert len(merged) == 1
    assert merged[0].end_number == 10


def test_natural_language_join_handles_empty_list() -> None:
    assert natural_language_join([]) == ""


def test_build_section_text_with_responsive_ranges() -> None:
    assert (
        build_section_text("RFP 01", ["EXAMPLE_000001-0005", "EXAMPLE_000010"])
        == "RFP 01:\nEXAMPLE_000001-0005 and EXAMPLE_000010"
    )


def test_decode_csv_bytes_handles_utf8_bom() -> None:
    raw = "﻿hello".encode("utf-8")
    assert decode_csv_bytes(raw) == "hello"


def test_decode_csv_bytes_falls_back_to_cp1252_for_smart_quotes() -> None:
    # 0x93/0x94 are valid cp1252 smart quotes but invalid as utf-8.
    raw = b"abc\x93def\x94"
    decoded = decode_csv_bytes(raw)
    assert "abc" in decoded
    assert "def" in decoded


def test_convert_csv_bytes_rejects_empty_file() -> None:
    with pytest.raises(ConversionError, match="empty"):
        convert_csv_bytes("empty.csv", b"")


def test_convert_csv_bytes_rejects_csv_with_fewer_than_three_columns() -> None:
    with pytest.raises(ConversionError, match="at least three columns"):
        convert_csv_bytes("two.csv", b"Begin,End\nEXAMPLE_000001,EXAMPLE_000001\n")


def test_convert_csv_bytes_rejects_csv_with_no_tag_columns() -> None:
    csv_text = "Begin,End,Notes\nEXAMPLE_000001,EXAMPLE_000001,whatever\n"
    with pytest.raises(ConversionError, match="No RFP or ROG tag columns"):
        convert_csv_bytes("notags.csv", csv_text.encode("utf-8"))


def test_convert_csv_bytes_skips_rows_with_mismatched_prefixes() -> None:
    csv_text = """Begin,End,Tag: RFP 01
ALPHA_000001,BETA_000002,TRUE
GAMMA_000005,GAMMA_000003,TRUE
"""
    result = convert_csv_bytes("mixed.csv", csv_text.encode("utf-8"))

    assert result.sections[0].text == "RFP 01:\nNo responsive documents."
    assert any("prefixes do not match" in warning for warning in result.warnings)
    assert any("after end Bates" in warning for warning in result.warnings)
    assert result.stats.total_rows == 2
    assert result.stats.skipped_rows == 2


def test_convert_csv_bytes_ignores_blank_rows_and_unflagged_rows() -> None:
    csv_text = """Begin,End,Tag: RFP 01
EXAMPLE_000001,EXAMPLE_000001,
,,

EXAMPLE_000002,EXAMPLE_000002,TRUE
"""
    result = convert_csv_bytes("blanks.csv", csv_text.encode("utf-8"))

    # Two non-blank data rows are counted; one is unflagged so contributes nothing.
    assert result.stats.total_rows == 2
    assert result.warnings == []
    assert result.sections[0].text == "RFP 01:\nEXAMPLE_000002"


def test_convert_csv_bytes_default_filename_when_blank() -> None:
    csv_text = "Begin,End,Tag: RFP 01\nEXAMPLE_000001,EXAMPLE_000001,TRUE\n"
    result = convert_csv_bytes("", csv_text.encode("utf-8"))

    assert result.sourceFilename == "uploaded.csv"
    assert result.downloadFilename == "converted.txt"


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

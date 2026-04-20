from __future__ import annotations

import csv
import io
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from app.models import ConversionResponse, ConversionStats, SectionResult

HEADER_PATTERN = re.compile(r"\b(?P<label>(?:RFP|ROG)\s*(?P<number>\d+))\b", re.IGNORECASE)
BATES_PATTERN = re.compile(r"^(?P<prefix>.+?)_(?P<number>\d+)$")


class ConversionError(ValueError):
    """Raised when a CSV cannot be converted at the file level."""


@dataclass(frozen=True)
class TagColumn:
    index: int
    label: str


@dataclass(frozen=True)
class BatesValue:
    token: str
    prefix: str
    number: int
    width: int


@dataclass
class BatesInterval:
    prefix: str
    start_number: int
    end_number: int
    start_token: str
    end_width: int


def extract_tag_label(header: str) -> str | None:
    match = HEADER_PATTERN.search(header)
    if not match:
        return None

    prefix = match.group("label").split()[0].upper()
    number = match.group("number")
    return f"{prefix} {number}"


def parse_bates_value(token: str) -> BatesValue:
    trimmed = token.strip()
    match = BATES_PATTERN.match(trimmed)
    if not match:
        raise ConversionError(f"Invalid Bates token: {token!r}")

    number_text = match.group("number")
    return BatesValue(
        token=trimmed,
        prefix=match.group("prefix"),
        number=int(number_text),
        width=len(number_text),
    )


def render_interval(interval: BatesInterval) -> str:
    if interval.start_number == interval.end_number:
        return interval.start_token

    end_tail = str(interval.end_number).zfill(interval.end_width)[-min(4, interval.end_width) :]
    return f"{interval.start_token}-{end_tail}"


def natural_language_join(values: list[str]) -> str:
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return f"{', '.join(values[:-1])}, and {values[-1]}"


def merge_intervals(intervals: list[BatesInterval]) -> list[BatesInterval]:
    if not intervals:
        return []

    ordered = sorted(intervals, key=lambda interval: (interval.prefix, interval.start_number, interval.end_number))
    merged: list[BatesInterval] = []

    for interval in ordered:
        if not merged:
            merged.append(interval)
            continue

        current = merged[-1]
        if current.prefix == interval.prefix and interval.start_number <= current.end_number + 1:
            if interval.end_number >= current.end_number:
                current.end_number = interval.end_number
                current.end_width = interval.end_width
            continue

        merged.append(interval)

    return merged


def build_section_text(label: str, ranges: list[str]) -> str:
    body = natural_language_join(ranges) if ranges else "No responsive documents."
    return f"{label}:\n{body}"


def decode_csv_bytes(raw_bytes: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ConversionError("Unable to decode the uploaded CSV file.")


def convert_csv_bytes(filename: str, raw_bytes: bytes) -> ConversionResponse:
    content = decode_csv_bytes(raw_bytes)
    reader = csv.reader(io.StringIO(content, newline=""))

    try:
        header = next(reader)
    except StopIteration as exc:
        raise ConversionError("The uploaded CSV is empty.") from exc

    if len(header) < 3:
        raise ConversionError("The uploaded CSV must include at least three columns.")

    tag_columns = [
        TagColumn(index=index, label=label)
        for index, raw_header in enumerate(header[2:], start=2)
        if (label := extract_tag_label(raw_header))
    ]

    if not tag_columns:
        raise ConversionError("No RFP or ROG tag columns were found in the uploaded CSV.")

    intervals_by_label: dict[str, list[BatesInterval]] = defaultdict(list)
    warnings: list[str] = []
    total_rows = 0

    for row_number, row in enumerate(reader, start=2):
        if not row or not any(cell.strip() for cell in row):
            continue

        total_rows += 1

        responsive_labels = [
            column.label
            for column in tag_columns
            if column.index < len(row) and row[column.index].strip().upper() == "TRUE"
        ]

        if not responsive_labels:
            continue

        if len(row) < 2:
            warnings.append(f"Row {row_number} skipped: missing begin or end Bates value.")
            continue

        begin_raw = row[0].strip()
        end_raw = row[1].strip()

        try:
            begin = parse_bates_value(begin_raw)
            end = parse_bates_value(end_raw)
        except ConversionError as exc:
            warnings.append(f"Row {row_number} skipped: {exc}.")
            continue

        if begin.prefix != end.prefix:
            warnings.append(
                f"Row {row_number} skipped: begin/end Bates prefixes do not match ({begin.prefix} vs {end.prefix})."
            )
            continue

        if begin.number > end.number:
            warnings.append(
                f"Row {row_number} skipped: begin Bates {begin.token} is after end Bates {end.token}."
            )
            continue

        for label in responsive_labels:
            intervals_by_label[label].append(
                BatesInterval(
                    prefix=begin.prefix,
                    start_number=begin.number,
                    end_number=end.number,
                    start_token=begin.token,
                    end_width=end.width,
                )
            )

    sections: list[SectionResult] = []
    for column in tag_columns:
        merged = merge_intervals(intervals_by_label[column.label])
        rendered_ranges = [render_interval(interval) for interval in merged]
        sections.append(
            SectionResult(
                label=column.label,
                ranges=rendered_ranges,
                responsive=bool(rendered_ranges),
                text=build_section_text(column.label, rendered_ranges),
            )
        )

    with_empty = "\n\n".join(section.text for section in sections)
    without_empty_sections = [section.text for section in sections if section.responsive]
    without_empty = "\n\n".join(without_empty_sections)

    download_name = f"{Path(filename or 'converted').stem}.txt"

    return ConversionResponse(
        sourceFilename=filename or "uploaded.csv",
        downloadFilename=download_name,
        warnings=warnings,
        sections=sections,
        documentTextWithEmpty=with_empty,
        documentTextWithoutEmpty=without_empty,
        stats=ConversionStats(
            total_rows=total_rows,
            skipped_rows=len(warnings),
            total_sections=len(sections),
            responsive_sections=sum(1 for section in sections if section.responsive),
        ),
    )

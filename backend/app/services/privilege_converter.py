from __future__ import annotations

import csv
import io
import re
from collections.abc import Callable
from pathlib import Path

from app.models import PrivilegeConversionResponse, PrivilegeConversionStats

BEGIN_BATES_PREFIX = "Begin Bates num from "
END_BATES_PREFIX = "End Bates num from "
DOCUMENT_DATE_HEADER = "Document Date"
FILE_NAME_HEADER = "File Name"
EMAIL_SUBJECT_HEADER = "Email Subject"
EMAIL_FROM_HEADER = "Email From"
EMAIL_TO_HEADER = "Email To"
EMAIL_CC_HEADER = "Email CC"
EMAIL_BCC_HEADER = "Email BCC"
REDACT_HEADER = "Tag: Privilege - Redact"
WITHHOLD_HEADER = "Tag: Privilege - Withhold"
OUTPUT_HEADERS = [
    "Beginning No.",
    "End No.",
    "Date",
    "Description",
    "Author",
    "Recipient(s)",
    "Privilege",
]
TRUE_VALUE = "TRUE"
TRAILING_DIGITS_PATTERN = re.compile(r"^(?P<prefix>.*\D)(?P<digits>\d+)$")
REASON_LABELS = {
    "AC-WP": "Attorney Client Privilege",
}


class ConversionError(ValueError):
    """Raised when a privilege CSV cannot be converted."""


def decode_csv_bytes(raw_bytes: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ConversionError("Unable to decode the uploaded CSV file.")


def is_truthy(value: str | None) -> bool:
    return (value or "").strip().upper() == TRUE_VALUE


def normalize_bates_token(token: str, *, row_number: int, column_label: str, warnings: list[str]) -> str:
    trimmed = token.strip()
    if not trimmed:
        warnings.append(f"Row {row_number} {column_label} Bates value is blank and was left unchanged.")
        return trimmed

    match = TRAILING_DIGITS_PATTERN.match(trimmed)
    if not match:
        warnings.append(f"Row {row_number} {column_label} Bates value {trimmed!r} could not be normalized.")
        return trimmed

    prefix = match.group("prefix")
    digits = match.group("digits")
    separator = "" if prefix.endswith("_") else "_"
    return f"{prefix}{separator}{digits}"


def friendly_reason_label(header: str) -> str:
    label = header.strip()
    if label.startswith("Tag:"):
        label = label.removeprefix("Tag:").strip()
    return REASON_LABELS.get(label, label)


def require_header(fieldnames: list[str], *, label: str, predicate: Callable[[str], bool] | None = None) -> str:
    if predicate is None:
        predicate = lambda candidate: candidate == label

    for header in fieldnames:
        if predicate(header.strip()):
            return header

    raise ConversionError(f"The uploaded CSV is missing the required column {label!r}.")


def resolve_headers(fieldnames: list[str]) -> tuple[dict[str, str], list[str]]:
    if not fieldnames:
        raise ConversionError("The uploaded CSV is empty.")

    begin_header = require_header(
        fieldnames,
        label=BEGIN_BATES_PREFIX,
        predicate=lambda candidate: candidate.startswith(BEGIN_BATES_PREFIX),
    )
    end_header = require_header(
        fieldnames,
        label=END_BATES_PREFIX,
        predicate=lambda candidate: candidate.startswith(END_BATES_PREFIX),
    )

    required_headers = {
        "begin": begin_header,
        "end": end_header,
        "date": require_header(fieldnames, label=DOCUMENT_DATE_HEADER),
        "file_name": require_header(fieldnames, label=FILE_NAME_HEADER),
        "email_subject": require_header(fieldnames, label=EMAIL_SUBJECT_HEADER),
        "email_from": require_header(fieldnames, label=EMAIL_FROM_HEADER),
        "email_to": require_header(fieldnames, label=EMAIL_TO_HEADER),
        "email_cc": require_header(fieldnames, label=EMAIL_CC_HEADER),
        "email_bcc": require_header(fieldnames, label=EMAIL_BCC_HEADER),
        "redact": require_header(fieldnames, label=REDACT_HEADER),
        "withhold": require_header(fieldnames, label=WITHHOLD_HEADER),
    }

    stripped_headers = [header.strip() for header in fieldnames]
    withhold_index = stripped_headers.index(WITHHOLD_HEADER)
    reason_headers = fieldnames[withhold_index + 1 :]
    if not reason_headers:
        raise ConversionError(
            "The uploaded CSV must include at least one privilege reason column after "
            f"{WITHHOLD_HEADER!r}."
        )

    return required_headers, reason_headers


def render_privilege_value(status_label: str, reason_headers: list[str]) -> str:
    reasons = [friendly_reason_label(header) for header in reason_headers]
    return f"{status_label} - {'; '.join(reasons)}"


def render_row_bates_context(row: dict[str, str], headers: dict[str, str], *, row_number: int) -> str:
    begin_value = (row.get(headers["begin"]) or "").strip() or "<blank>"
    end_value = (row.get(headers["end"]) or "").strip() or "<blank>"
    return f"Row {row_number} [{begin_value}]-[{end_value}]"


def build_csv_text(headers: list[str], rows: list[list[str]]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(headers)
    writer.writerows(rows)
    return buffer.getvalue()


def convert_csv_bytes(filename: str, raw_bytes: bytes) -> PrivilegeConversionResponse:
    content = decode_csv_bytes(raw_bytes)
    reader = csv.DictReader(io.StringIO(content, newline=""))
    headers, reason_headers = resolve_headers(reader.fieldnames or [])

    output_rows: list[list[str]] = []
    warnings: list[str] = []
    total_rows = 0

    for row_number, row in enumerate(reader, start=2):
        if not row or not any((value or "").strip() for value in row.values()):
            continue

        total_rows += 1

        redact_selected = is_truthy(row.get(headers["redact"]))
        withhold_selected = is_truthy(row.get(headers["withhold"]))
        if redact_selected == withhold_selected:
            raise ConversionError(
                f"Row {row_number} must have exactly one of {REDACT_HEADER!r} or {WITHHOLD_HEADER!r} set to TRUE."
            )

        selected_reason_headers = [header for header in reason_headers if is_truthy(row.get(header))]
        if not selected_reason_headers:
            raise ConversionError(
                f"{render_row_bates_context(row, headers, row_number=row_number)} must include at least one "
                "privilege reason marked TRUE."
            )

        description = (row.get(headers["email_subject"]) or "").strip() or (row.get(headers["file_name"]) or "").strip()
        recipients = [
            (row.get(headers["email_to"]) or "").strip(),
            (row.get(headers["email_cc"]) or "").strip(),
            (row.get(headers["email_bcc"]) or "").strip(),
        ]
        recipient_value = "; ".join(value for value in recipients if value)

        status_label = "Redacted" if redact_selected else "Withheld"
        output_rows.append(
            [
                normalize_bates_token(
                    row.get(headers["begin"]) or "",
                    row_number=row_number,
                    column_label="Beginning",
                    warnings=warnings,
                ),
                normalize_bates_token(
                    row.get(headers["end"]) or "",
                    row_number=row_number,
                    column_label="End",
                    warnings=warnings,
                ),
                row.get(headers["date"]) or "",
                description,
                row.get(headers["email_from"]) or "",
                recipient_value,
                render_privilege_value(status_label, selected_reason_headers),
            ]
        )

    download_name = f"{Path(filename or 'converted').stem}-privilege-log.csv"

    return PrivilegeConversionResponse(
        sourceFilename=filename or "uploaded.csv",
        downloadFilename=download_name,
        headers=OUTPUT_HEADERS,
        rows=output_rows,
        csvText=build_csv_text(OUTPUT_HEADERS, output_rows),
        warnings=warnings,
        stats=PrivilegeConversionStats(
            total_rows=total_rows,
            exported_rows=len(output_rows),
            reason_columns=len(reason_headers),
        ),
    )

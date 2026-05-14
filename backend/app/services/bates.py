from __future__ import annotations


def render_compact_range_end(number: int, source_width: int) -> str:
    full_number = str(number).zfill(source_width)
    significant_digits = full_number.lstrip("0") or "0"

    if source_width >= 4:
        return significant_digits.zfill(4)

    return significant_digits

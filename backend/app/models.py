from __future__ import annotations

from pydantic import BaseModel, Field


class SectionResult(BaseModel):
    label: str = Field(..., description="Normalized section label, such as RFP 01.")
    ranges: list[str] = Field(default_factory=list, description="Rendered Bates ranges for the section.")
    responsive: bool = Field(..., description="Whether the section has at least one responsive row.")
    text: str = Field(..., description="Rendered section text.")


class ConversionStats(BaseModel):
    total_rows: int
    skipped_rows: int
    total_sections: int
    responsive_sections: int


class ConversionResponse(BaseModel):
    sourceFilename: str
    downloadFilename: str
    warnings: list[str] = Field(default_factory=list)
    sections: list[SectionResult]
    documentTextWithEmpty: str
    documentTextWithoutEmpty: str
    stats: ConversionStats


class PrivilegeConversionStats(BaseModel):
    total_rows: int
    exported_rows: int
    reason_columns: int


class PrivilegeConversionResponse(BaseModel):
    sourceFilename: str
    downloadFilename: str
    headers: list[str]
    rows: list[list[str]]
    csvText: str
    warnings: list[str] = Field(default_factory=list)
    stats: PrivilegeConversionStats

"""Pydantic schemas for the metadata forensics report."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ExtractedMetadata(BaseModel):
    """Metadata fields pulled from the document."""

    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    file_size_human: Optional[str] = None
    file_type: Optional[str] = None
    pdf_version: Optional[str] = None
    page_count: Optional[int] = None
    encrypted: Optional[bool] = None
    encryption_method: Optional[str] = None

    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None

    created_at: Optional[str] = None
    modified_at: Optional[str] = None

    has_xmp: Optional[bool] = None
    xmp_create_date: Optional[str] = None
    xmp_modify_date: Optional[str] = None
    xmp_creator_tool: Optional[str] = None
    xmp_producer: Optional[str] = None

    incremental_updates: Optional[int] = Field(
        default=None,
        description="Approximate number of incremental save sections detected.",
    )

    raw_info: dict[str, Any] = Field(default_factory=dict)


class Finding(BaseModel):
    """A single rule-based observation."""

    id: str
    title: str
    severity: str  # "Low" | "Medium" | "High"
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str
    technical_explanation: Optional[str] = None
    simple_explanation: Optional[str] = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class AnalysisReport(BaseModel):
    """The full forensics report returned to the client."""

    document_name: str
    file_type: str
    metadata_risk_score: int = Field(ge=0, le=100)
    metadata_risk_level: str  # "Low" | "Medium" | "High"
    summary: str
    extracted_metadata: ExtractedMetadata
    findings: list[Finding]
    recommended_action: str


class MetadataDifference(BaseModel):
    """Single field-level difference between two reports."""

    field: str
    file_a_value: Any = None
    file_b_value: Any = None
    note: str


class ComparisonReport(BaseModel):
    """Comparison payload for two uploaded files."""

    file_a_report: AnalysisReport
    file_b_report: AnalysisReport
    differences: list[MetadataDifference]
    summary: str

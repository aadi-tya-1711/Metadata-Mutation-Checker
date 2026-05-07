"""High-level analyzer that ties extraction, rules, and scoring together."""

from __future__ import annotations

from .extractors import extract_image_metadata, extract_pdf_metadata
from .rules import run_all_rules
from .schemas import (
    AnalysisReport,
    ComparisonReport,
    ExtractedMetadata,
    MetadataDifference,
)
from .scoring import build_summary, compute_risk_score, recommended_action, risk_level


def analyze_document(
    raw: bytes,
    file_name: str,
    content_type: str | None,
) -> AnalysisReport:
    """Produce a full :class:`AnalysisReport` for the supplied document."""
    ct = (content_type or "").lower()
    is_pdf = ct == "application/pdf" or file_name.lower().endswith(".pdf")
    is_image = ct.startswith("image/") or file_name.lower().endswith(
        (".jpg", ".jpeg", ".png", ".tiff", ".tif")
    )

    if is_pdf:
        meta_dict = extract_pdf_metadata(raw, file_name)
    elif is_image:
        meta_dict = extract_image_metadata(raw, file_name, ct)
    else:
        meta_dict = {
            "file_name": file_name,
            "file_size_bytes": len(raw),
            "file_type": ct or "application/octet-stream",
            "raw_info": {"note": "Unsupported file type for full analysis."},
        }

    findings = run_all_rules(meta_dict) if is_pdf else []
    score = compute_risk_score(findings)
    level = risk_level(score)

    extracted = ExtractedMetadata(**{
        k: v for k, v in meta_dict.items()
        if k in ExtractedMetadata.model_fields
    })

    report = AnalysisReport(
        document_name=meta_dict.get("file_name") or file_name,
        file_type=meta_dict.get("file_type") or (ct or "unknown"),
        metadata_risk_score=score,
        metadata_risk_level=level,
        summary=build_summary(level, findings, score),
        extracted_metadata=extracted,
        findings=findings,
        recommended_action=recommended_action(level, findings),
    )
    _attach_explanation_modes(report)
    return report


def _to_simple_explanation(text: str) -> str:
    """Convert technical wording to a clearer non-technical variant."""
    if not text:
        return text
    replacements = {
        "document information dictionary": "document metadata",
        "incrementally saved": "saved multiple times",
        "originator tool": "original authoring tool",
        "producer field": "export tool field",
        "creation date": "first saved date",
        "modification date": "last saved date",
        "warrants review": "is worth checking",
    }
    out = text
    for old, new in replacements.items():
        out = out.replace(old, new)
    return out


def _attach_explanation_modes(report: AnalysisReport) -> None:
    """Populate technical and simple explanation fields for each finding."""
    for f in report.findings:
        f.technical_explanation = f.explanation
        f.simple_explanation = _to_simple_explanation(f.explanation)


def _metadata_differences(a: AnalysisReport, b: AnalysisReport) -> list[MetadataDifference]:
    """Compute extracted metadata differences for two reports."""
    a_meta = a.extracted_metadata.model_dump()
    b_meta = b.extracted_metadata.model_dump()
    fields = sorted(set(a_meta.keys()) | set(b_meta.keys()))
    diffs: list[MetadataDifference] = []
    for field in fields:
        av = a_meta.get(field)
        bv = b_meta.get(field)
        if av != bv:
            diffs.append(
                MetadataDifference(
                    field=field,
                    file_a_value=av,
                    file_b_value=bv,
                    note=(
                        "Values differ between files; this may reflect different "
                        "export paths, edits, or metadata stripping."
                    ),
                )
            )
    return diffs


def compare_documents(
    raw_a: bytes,
    file_name_a: str,
    content_type_a: str | None,
    raw_b: bytes,
    file_name_b: str,
    content_type_b: str | None,
) -> ComparisonReport:
    """Analyze two files and return their metadata differences."""
    a = analyze_document(raw_a, file_name_a, content_type_a)
    b = analyze_document(raw_b, file_name_b, content_type_b)
    diffs = _metadata_differences(a, b)
    summary = (
        f"Compared '{a.document_name}' and '{b.document_name}'. "
        f"{len(diffs)} extracted metadata field differences were observed."
    )
    return ComparisonReport(
        file_a_report=a,
        file_b_report=b,
        differences=diffs,
        summary=summary,
    )

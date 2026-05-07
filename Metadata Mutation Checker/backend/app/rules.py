"""Rule-based metadata checks.

Every rule returns a list of :class:`Finding`. Rules are deliberately written
to be conservative — language is hedged and findings are *observations*, not
verdicts. The downstream scorer is responsible for combining them into a
risk picture; rules themselves never claim "tampering".
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Iterable, Optional

from .schemas import Finding


# Categorisation of common tool strings. We use lowercase substring matching.
EDITING_TOOLS = {
    # name -> (category, severity-hint)
    "acrobat": "Adobe Acrobat (full editor)",
    "adobe acrobat": "Adobe Acrobat (full editor)",
    "preview": "Apple Preview (can edit & re-save)",
    "canva": "Canva (online design tool)",
    "photoshop": "Adobe Photoshop (image editor)",
    "illustrator": "Adobe Illustrator",
    "indesign": "Adobe InDesign",
    "ilovepdf": "iLovePDF (online editor)",
    "smallpdf": "Smallpdf (online editor)",
    "pdfescape": "PDFescape (online editor)",
    "sejda": "Sejda (online editor)",
    "pdf-xchange": "PDF-XChange Editor",
    "foxit": "Foxit (PDF editor)",
    "nitro": "Nitro PDF",
    "wondershare": "Wondershare PDFelement",
    "pdfsam": "PDFsam",
    "soda pdf": "Soda PDF",
}

ORIGINATOR_TOOLS = {
    "microsoft® word",
    "microsoft word",
    "microsoft® excel",
    "microsoft excel",
    "microsoft® powerpoint",
    "microsoft powerpoint",
    "libreoffice",
    "openoffice",
    "google docs",
    "pages",
    "latex",
    "pdftex",
    "xetex",
    "tex live",
    "texlive",
    "miktex",
    "quartz pdfcontext",
    "skia/pdf",
    "chromium",
    "chrome",
    "wkhtmltopdf",
    "reportlab",
    "tcpdf",
    "fpdf",
    "itext",
    "prince",
    "weasyprint",
    "ghostscript",
    "pypdf",
}


def _matches_any(text: Optional[str], needles: Iterable[str]) -> Optional[str]:
    if not text:
        return None
    low = text.lower()
    for n in needles:
        if n in low:
            return n
    return None


def _identify_editor(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    low = text.lower()
    for needle, label in EDITING_TOOLS.items():
        if needle in low:
            return label
    return None


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _norm(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def rule_missing_critical_fields(meta: dict[str, Any]) -> list[Finding]:
    """Flag missing/empty critical fields."""
    findings: list[Finding] = []

    critical = {
        "title": "Title",
        "author": "Author",
        "creator": "Creator",
        "producer": "Producer",
        "created_at": "Creation date",
        "modified_at": "Modification date",
    }
    missing = [label for key, label in critical.items() if not meta.get(key)]
    if not missing:
        return findings

    if len(missing) >= 4:
        findings.append(
            Finding(
                id="missing_many_fields",
                title="Several core metadata fields are missing",
                severity="Medium",
                confidence=0.6,
                explanation=(
                    "Multiple standard metadata fields ("
                    + ", ".join(missing)
                    + ") are absent. This may indicate the document was "
                    "stripped of metadata, exported from a tool that does "
                    "not write these fields, or processed by a converter. "
                    "It warrants review but is not, on its own, evidence "
                    "of modification."
                ),
                evidence={"missing": missing},
            )
        )
    elif missing:
        findings.append(
            Finding(
                id="missing_some_fields",
                title="Some optional metadata fields are missing",
                severity="Low",
                confidence=0.4,
                explanation=(
                    "The fields "
                    + ", ".join(missing)
                    + " are not populated. This is common for documents "
                    "exported by simple tools and is generally benign, "
                    "though it reduces what can be cross-checked."
                ),
                evidence={"missing": missing},
            )
        )
    return findings


def rule_date_anomalies(meta: dict[str, Any]) -> list[Finding]:
    """Check for missing dates, modified-before-created, and large gaps."""
    findings: list[Finding] = []
    created = _parse_iso(meta.get("created_at"))
    modified = _parse_iso(meta.get("modified_at"))

    if not created and not modified:
        findings.append(
            Finding(
                id="dates_both_missing",
                title="Both creation and modification dates are missing",
                severity="Medium",
                confidence=0.55,
                explanation=(
                    "Neither a creation nor a modification date is present "
                    "in the document information dictionary. Some exporters "
                    "deliberately omit dates, but the absence also removes "
                    "an important consistency signal and could suggest the "
                    "metadata was stripped."
                ),
                evidence={},
            )
        )
        return findings

    if created and not modified:
        findings.append(
            Finding(
                id="modified_missing",
                title="Modification date is missing",
                severity="Low",
                confidence=0.35,
                explanation=(
                    "A creation date is present but no modification date is "
                    "recorded. This is common for documents exported once "
                    "and never re-saved."
                ),
                evidence={"created_at": meta.get("created_at")},
            )
        )

    if modified and not created:
        findings.append(
            Finding(
                id="created_missing",
                title="Creation date is missing while a modification date is present",
                severity="Medium",
                confidence=0.6,
                explanation=(
                    "A modification date is recorded but the original "
                    "creation date is absent. This pattern can occur when "
                    "metadata is partially overwritten and warrants review."
                ),
                evidence={"modified_at": meta.get("modified_at")},
            )
        )

    if created and modified:
        # Compare in UTC where possible; if either is naive, compare naive.
        a, b = created, modified
        try:
            if a.tzinfo and not b.tzinfo:
                b = b.replace(tzinfo=a.tzinfo)
            elif b.tzinfo and not a.tzinfo:
                a = a.replace(tzinfo=b.tzinfo)
        except Exception:
            pass

        try:
            delta = b - a
        except Exception:
            delta = None

        if delta is not None and delta.total_seconds() < -60:
            findings.append(
                Finding(
                    id="modified_before_created",
                    title="Modification date appears earlier than creation date",
                    severity="High",
                    confidence=0.85,
                    explanation=(
                        "The recorded modification date is earlier than the "
                        "creation date by "
                        f"{abs(int(delta.total_seconds() // 60))} minutes. "
                        "While clock skew or timezone bugs in exporters can "
                        "explain small inversions, a meaningful inversion is "
                        "consistent with metadata being edited and warrants "
                        "careful review."
                    ),
                    evidence={
                        "created_at": meta.get("created_at"),
                        "modified_at": meta.get("modified_at"),
                        "delta_seconds": int(delta.total_seconds()),
                    },
                )
            )
        elif delta is not None and delta > timedelta(days=365 * 5):
            findings.append(
                Finding(
                    id="dates_large_gap",
                    title="Unusually large gap between creation and modification dates",
                    severity="Medium",
                    confidence=0.5,
                    explanation=(
                        f"The document records a gap of {delta.days} days "
                        "between creation and last modification. Long-lived "
                        "documents do exist, but very large gaps could "
                        "suggest the file has been re-saved years after the "
                        "original was authored."
                    ),
                    evidence={"gap_days": delta.days},
                )
            )

    return findings


def rule_creator_producer_mismatch(meta: dict[str, Any]) -> list[Finding]:
    """Flag unusual creator/producer combinations."""
    findings: list[Finding] = []
    creator = _norm(meta.get("creator"))
    producer = _norm(meta.get("producer"))

    if not creator and not producer:
        return findings

    creator_editor = _identify_editor(creator)
    producer_editor = _identify_editor(producer)
    creator_originator = _matches_any(creator, ORIGINATOR_TOOLS)
    producer_originator = _matches_any(producer, ORIGINATOR_TOOLS)

    # Originator + Editor is the classic "edited after creation" signal.
    if creator_originator and producer_editor:
        findings.append(
            Finding(
                id="creator_originator_producer_editor",
                title="Creator looks like an originator, producer looks like an editor",
                severity="Medium",
                confidence=0.65,
                explanation=(
                    f"The creator field references an originator tool "
                    f"('{meta.get('creator')}') while the producer field "
                    f"references an editing tool ('{meta.get('producer')}'). "
                    "This pattern is consistent with a document that was "
                    "produced from a source application and later re-saved "
                    "through an editor — which is normal in many workflows "
                    "but does mean the file is not in its original form."
                ),
                evidence={
                    "creator": meta.get("creator"),
                    "producer": meta.get("producer"),
                },
            )
        )

    # Two completely different editors is unusual.
    if (
        creator_editor
        and producer_editor
        and creator_editor != producer_editor
    ):
        findings.append(
            Finding(
                id="creator_producer_editor_mismatch",
                title="Creator and producer reference different editing tools",
                severity="Medium",
                confidence=0.55,
                explanation=(
                    f"Creator ('{creator_editor}') and producer "
                    f"('{producer_editor}') reference different editing "
                    "applications. This may indicate the document passed "
                    "through more than one editor, which warrants review."
                ),
                evidence={
                    "creator": meta.get("creator"),
                    "producer": meta.get("producer"),
                },
            )
        )

    # Plain disagreement — only flag at low severity since it is extremely
    # common for legitimate exports (e.g. Word + Adobe PDF Library).
    if (
        creator
        and producer
        and creator != producer
        and not (creator_originator and producer_originator)
        and not (creator_originator and producer_editor)
        and not (creator_editor and producer_editor)
    ):
        findings.append(
            Finding(
                id="creator_producer_differ",
                title="Creator and producer fields differ",
                severity="Low",
                confidence=0.25,
                explanation=(
                    "The creator and producer strings differ. This is "
                    "common in normal export pipelines (for example, an "
                    "authoring tool plus a PDF library) but is recorded "
                    "here for completeness."
                ),
                evidence={
                    "creator": meta.get("creator"),
                    "producer": meta.get("producer"),
                },
            )
        )

    return findings


def rule_known_editor_detected(meta: dict[str, Any]) -> list[Finding]:
    """Surface when a recognised editor signature appears anywhere."""
    findings: list[Finding] = []
    haystacks = {
        "creator": meta.get("creator"),
        "producer": meta.get("producer"),
        "xmp_creator_tool": meta.get("xmp_creator_tool"),
        "xmp_producer": meta.get("xmp_producer"),
    }

    seen: dict[str, list[str]] = {}
    for field, value in haystacks.items():
        label = _identify_editor(value)
        if label:
            seen.setdefault(label, []).append(field)

    if not seen:
        return findings

    for label, fields in seen.items():
        findings.append(
            Finding(
                id=f"editor_detected:{label}".lower().replace(" ", "_"),
                title=f"Editing tool fingerprint detected: {label}",
                severity="Medium",
                confidence=0.6,
                explanation=(
                    f"The metadata references {label}, an application "
                    "capable of modifying PDFs. This does not by itself "
                    "indicate the content was altered — many users save "
                    "PDFs through such tools routinely — but it does mean "
                    "the file has been processed by an editor at some "
                    "point, which is worth noting."
                ),
                evidence={"matched_in": fields, "tool": label},
            )
        )
    return findings


def rule_xmp_vs_info_mismatch(meta: dict[str, Any]) -> list[Finding]:
    """Bonus rule: compare XMP packet against the document info dict."""
    findings: list[Finding] = []
    if not meta.get("has_xmp"):
        return findings

    pairs = [
        (
            "creator/producer",
            (meta.get("creator"), meta.get("producer")),
            (meta.get("xmp_creator_tool"), meta.get("xmp_producer")),
        ),
    ]

    info_creator = _norm(meta.get("creator"))
    xmp_creator = _norm(meta.get("xmp_creator_tool"))
    info_producer = _norm(meta.get("producer"))
    xmp_producer = _norm(meta.get("xmp_producer"))

    diffs: list[str] = []
    if info_creator and xmp_creator and info_creator != xmp_creator:
        diffs.append(
            f"creator: info='{meta.get('creator')}' vs xmp='{meta.get('xmp_creator_tool')}'"
        )
    if info_producer and xmp_producer and info_producer != xmp_producer:
        diffs.append(
            f"producer: info='{meta.get('producer')}' vs xmp='{meta.get('xmp_producer')}'"
        )

    info_create = _parse_iso(meta.get("created_at"))
    xmp_create = _parse_iso(meta.get("xmp_create_date"))
    if info_create and xmp_create:
        try:
            gap = abs((info_create - xmp_create.replace(tzinfo=info_create.tzinfo)).total_seconds())
        except Exception:
            gap = 0
        if gap > 60:
            diffs.append(
                f"create date differs by {int(gap)}s "
                f"(info={meta.get('created_at')}, xmp={meta.get('xmp_create_date')})"
            )

    if diffs:
        findings.append(
            Finding(
                id="xmp_info_mismatch",
                title="XMP metadata differs from document information dictionary",
                severity="Medium",
                confidence=0.6,
                explanation=(
                    "The XMP packet and the legacy document information "
                    "dictionary disagree on one or more fields. PDF readers "
                    "are expected to keep these in sync; divergence can "
                    "occur after partial edits and warrants review."
                ),
                evidence={"differences": diffs},
            )
        )
    return findings


def rule_incremental_updates(meta: dict[str, Any]) -> list[Finding]:
    """Flag incremental save markers (multiple ``%%EOF`` segments)."""
    findings: list[Finding] = []
    n = meta.get("incremental_updates") or 0
    if n <= 0:
        return findings

    sev = "Low" if n == 1 else "Medium"
    conf = 0.45 if n == 1 else 0.7
    findings.append(
        Finding(
            id="incremental_updates",
            title=f"Incremental updates detected ({n} additional save marker{'s' if n != 1 else ''})",
            severity=sev,
            confidence=conf,
            explanation=(
                f"The file contains {n + 1} %%EOF marker(s), suggesting "
                "the PDF has been incrementally saved one or more times. "
                "Incremental updates are a normal feature of PDF "
                "(used for annotations, signatures, form-filling) but "
                "they do mean the current file is not byte-identical to "
                "its original release."
            ),
            evidence={"incremental_updates": n},
        )
    )
    return findings


def rule_encryption(meta: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    if meta.get("encrypted"):
        findings.append(
            Finding(
                id="encrypted",
                title="Document is encrypted",
                severity="Low",
                confidence=0.4,
                explanation=(
                    "The PDF is encrypted. Encryption is a legitimate "
                    "feature used to restrict editing or printing, but it "
                    "limits how thoroughly the structure can be inspected "
                    "and reduces the confidence of other checks."
                ),
                evidence={},
            )
        )
    return findings


def rule_structural_parse_error(meta: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    err = (meta.get("raw_info") or {}).get("parse_error")
    if err:
        findings.append(
            Finding(
                id="parse_error",
                title="Document could not be fully parsed",
                severity="Medium",
                confidence=0.5,
                explanation=(
                    "The PDF parser reported a structural issue while "
                    f"reading the file ('{err}'). This may indicate a "
                    "truncated or unusual file and could suggest manual "
                    "modification, but many legitimate PDFs also produce "
                    "warnings."
                ),
                evidence={"parse_error": err},
            )
        )
    return findings


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

ALL_RULES = (
    rule_missing_critical_fields,
    rule_date_anomalies,
    rule_creator_producer_mismatch,
    rule_known_editor_detected,
    rule_xmp_vs_info_mismatch,
    rule_incremental_updates,
    rule_encryption,
    rule_structural_parse_error,
)


def run_all_rules(meta: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for rule in ALL_RULES:
        try:
            findings.extend(rule(meta))
        except Exception as exc:  # pragma: no cover - defensive
            findings.append(
                Finding(
                    id=f"rule_error:{rule.__name__}",
                    title=f"Internal rule error: {rule.__name__}",
                    severity="Low",
                    confidence=0.0,
                    explanation=(
                        "A check could not be executed against this "
                        f"document ({exc}). The remaining checks still ran."
                    ),
                    evidence={"error": str(exc)},
                )
            )
    return findings

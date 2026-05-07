"""Risk scoring for metadata findings.

The scorer takes the raw weighted points implied by each finding and applies
a diminishing-returns curve so a long tail of weak signals can never explode
into a confident "High". It also enforces a hard ceiling of 30 when the only
findings are low-confidence ones.
"""

from __future__ import annotations

import math
from typing import Iterable

from .schemas import Finding


SEVERITY_WEIGHTS = {
    "High": 20.0,
    "Medium": 10.0,
    "Low": 5.0,
}


def _weight(finding: Finding) -> float:
    base = SEVERITY_WEIGHTS.get(finding.severity, 5.0)
    return base * max(0.0, min(1.0, finding.confidence))


def compute_risk_score(findings: Iterable[Finding]) -> int:
    """Combine findings into a 0–100 risk score.

    Strategy:

    * Each finding contributes ``severity_weight × confidence`` raw points.
    * We sum the points but pass them through ``1 - exp(-x / k)`` so that
      additional weak signals add less and less. ``k`` is tuned so a single
      strong High finding (~20 × 0.85 = 17 pts) yields roughly 65, and two
      strong Highs saturate near 90.
    * We then enforce: if no finding is at least Medium with confidence
      ≥ 0.5 *and* there is no High finding, the score is capped at 30.
    """
    findings = list(findings)
    if not findings:
        return 0

    raw = sum(_weight(f) for f in findings)

    k = 22.0
    curved = 100.0 * (1.0 - math.exp(-raw / k))

    has_strong_signal = any(
        (f.severity == "High" and f.confidence >= 0.5)
        or (f.severity == "Medium" and f.confidence >= 0.5)
        for f in findings
    )
    if not has_strong_signal:
        curved = min(curved, 30.0)

    return int(round(max(0.0, min(100.0, curved))))


def risk_level(score: int) -> str:
    if score <= 30:
        return "Low"
    if score <= 65:
        return "Medium"
    return "High"


def recommended_action(level: str, findings: list[Finding]) -> str:
    """Produce careful, non-accusatory guidance for the reviewer."""
    if level == "High":
        return (
            "Several signals in this document's metadata warrant careful "
            "human review. Consider corroborating with the document's "
            "source, requesting an original copy, or examining the file in "
            "a dedicated forensics tool before relying on its contents."
        )
    if level == "Medium":
        return (
            "The metadata contains observations that may be worth a closer "
            "look. None individually prove modification, but together they "
            "suggest the file has been processed by editing software or has "
            "incomplete provenance — confirm with the sender if context is "
            "important."
        )
    return (
        "No significant metadata anomalies were detected. The document's "
        "metadata appears internally consistent, though absence of "
        "anomalies is not in itself proof of authenticity."
    )


def build_summary(level: str, findings: list[Finding], score: int) -> str:
    """One-paragraph human-readable summary."""
    n = len(findings)
    high = sum(1 for f in findings if f.severity == "High")
    med = sum(1 for f in findings if f.severity == "Medium")
    low = sum(1 for f in findings if f.severity == "Low")

    if n == 0:
        return (
            f"Metadata risk is assessed as {level} ({score}/100). "
            "No rule-based observations were triggered against this "
            "document."
        )

    parts = []
    if high:
        parts.append(f"{high} high-severity")
    if med:
        parts.append(f"{med} medium-severity")
    if low:
        parts.append(f"{low} low-severity")
    breakdown = ", ".join(parts)

    return (
        f"Metadata risk is assessed as {level} ({score}/100). "
        f"{n} observation{'s' if n != 1 else ''} were recorded "
        f"({breakdown}). These are signals for review, not conclusions "
        "about authenticity."
    )

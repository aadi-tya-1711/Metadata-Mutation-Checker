"""Metadata extraction for PDF (and bonus image) documents.

The goal here is to pull as many useful fields as possible without ever raising
on a malformed file — every extractor degrades gracefully and returns ``None``
for anything it cannot determine.
"""

from __future__ import annotations

import io
import re
from datetime import datetime, timezone
from typing import Any, Optional
from xml.etree import ElementTree as ET

from pypdf import PdfReader
from pypdf.errors import PdfReadError


def _human_size(num_bytes: int) -> str:
    """Format a byte count as a short human-readable string."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024.0 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024.0
    return f"{size:.1f} GB"


_PDF_DATE_RE = re.compile(
    r"^D?:?(?P<year>\d{4})(?P<month>\d{2})?(?P<day>\d{2})?"
    r"(?P<hour>\d{2})?(?P<minute>\d{2})?(?P<second>\d{2})?"
    r"(?P<tz>[Z+\-]\d{0,2}'?\d{0,2}'?)?"
)


def parse_pdf_date(value: Any) -> Optional[str]:
    """Parse a PDF-style date (``D:YYYYMMDDHHmmSSOHH'mm'``) into ISO 8601.

    Returns ``None`` when the value cannot be parsed. Many PDF producers emit
    slightly different variants of this format — we try to be permissive.
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    m = _PDF_DATE_RE.match(s)
    if not m:
        return None
    parts = m.groupdict()
    try:
        year = int(parts["year"])
        month = int(parts["month"] or 1)
        day = int(parts["day"] or 1)
        hour = int(parts["hour"] or 0)
        minute = int(parts["minute"] or 0)
        second = int(parts["second"] or 0)
    except (TypeError, ValueError):
        return None

    tz_part = parts.get("tz") or ""
    tzinfo: Optional[timezone] = None
    if tz_part:
        if tz_part.startswith("Z"):
            tzinfo = timezone.utc
        else:
            sign = 1 if tz_part[0] == "+" else -1
            digits = re.findall(r"\d+", tz_part)
            tz_hours = int(digits[0]) if len(digits) >= 1 else 0
            tz_minutes = int(digits[1]) if len(digits) >= 2 else 0
            from datetime import timedelta

            offset = timedelta(hours=tz_hours, minutes=tz_minutes) * sign
            tzinfo = timezone(offset)

    try:
        dt = datetime(year, month, day, hour, minute, second, tzinfo=tzinfo)
    except ValueError:
        return None
    return dt.isoformat()


def _stringify(value: Any) -> Optional[str]:
    """Convert a pypdf metadata value to a clean string when sensible."""
    if value is None:
        return None
    try:
        s = str(value)
    except Exception:
        return None
    s = s.strip()
    return s or None


_XMP_NAMESPACES = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "dc": "http://purl.org/dc/elements/1.1/",
    "xmp": "http://ns.adobe.com/xap/1.0/",
    "pdf": "http://ns.adobe.com/pdf/1.3/",
    "xap": "http://ns.adobe.com/xap/1.0/",
}


def _xmp_text(elem: Optional[ET.Element]) -> Optional[str]:
    if elem is None:
        return None
    text = "".join(elem.itertext()).strip()
    return text or None


def parse_xmp(xmp_bytes: bytes) -> dict[str, Any]:
    """Extract a handful of useful XMP fields. Tolerant to malformed XML."""
    info: dict[str, Any] = {}
    if not xmp_bytes:
        return info
    try:
        root = ET.fromstring(xmp_bytes)
    except ET.ParseError:
        return info

    def find(path: str) -> Optional[ET.Element]:
        return root.find(path, _XMP_NAMESPACES)

    create = find(".//xmp:CreateDate") or find(".//xap:CreateDate")
    modify = find(".//xmp:ModifyDate") or find(".//xap:ModifyDate")
    creator_tool = find(".//xmp:CreatorTool") or find(".//xap:CreatorTool")
    producer = find(".//pdf:Producer")

    info["xmp_create_date"] = _xmp_text(create)
    info["xmp_modify_date"] = _xmp_text(modify)
    info["xmp_creator_tool"] = _xmp_text(creator_tool)
    info["xmp_producer"] = _xmp_text(producer)
    return info


# ---------------------------------------------------------------------------
# Structural checks
# ---------------------------------------------------------------------------

def count_eof_markers(raw: bytes) -> int:
    """Count ``%%EOF`` markers — multiple often indicate incremental saves."""
    return raw.count(b"%%EOF")


def detect_pdf_version(raw: bytes) -> Optional[str]:
    """Read the PDF version from the file header (e.g. ``%PDF-1.7``)."""
    head = raw[:32]
    m = re.search(rb"%PDF-(\d+\.\d+)", head)
    if not m:
        return None
    return m.group(1).decode("ascii", errors="ignore")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_pdf_metadata(raw: bytes, file_name: str) -> dict[str, Any]:
    """Extract metadata from a PDF file given its raw bytes and original name."""
    result: dict[str, Any] = {
        "file_name": file_name,
        "file_size_bytes": len(raw),
        "file_size_human": _human_size(len(raw)),
        "file_type": "application/pdf",
        "pdf_version": detect_pdf_version(raw),
        "raw_info": {},
    }

    eof_count = count_eof_markers(raw)
    result["incremental_updates"] = max(0, eof_count - 1)

    try:
        reader = PdfReader(io.BytesIO(raw))
    except PdfReadError as exc:
        result["raw_info"]["parse_error"] = str(exc)
        return result
    except Exception as exc:  # pragma: no cover - defensive
        result["raw_info"]["parse_error"] = f"unexpected: {exc}"
        return result

    # Encryption
    try:
        result["encrypted"] = bool(reader.is_encrypted)
        if reader.is_encrypted:
            # Try empty-password decrypt so we can still read page count / info.
            try:
                reader.decrypt("")
            except Exception:
                pass
    except Exception:
        result["encrypted"] = None

    # Page count
    try:
        result["page_count"] = len(reader.pages)
    except Exception:
        result["page_count"] = None

    # Document Info dictionary
    info = {}
    try:
        info = reader.metadata or {}
    except Exception:
        info = {}

    def _get(key: str) -> Optional[str]:
        try:
            return _stringify(info.get(key))
        except Exception:
            return None

    result["title"] = _get("/Title")
    result["author"] = _get("/Author")
    result["subject"] = _get("/Subject")
    result["keywords"] = _get("/Keywords")
    result["creator"] = _get("/Creator")
    result["producer"] = _get("/Producer")
    result["created_at"] = parse_pdf_date(_get("/CreationDate"))
    result["modified_at"] = parse_pdf_date(_get("/ModDate"))

    # Snapshot a few raw fields for transparency.
    try:
        for k, v in (info or {}).items():
            try:
                result["raw_info"][str(k)] = _stringify(v)
            except Exception:
                continue
    except Exception:
        pass

    # XMP metadata
    xmp_data: dict[str, Any] = {}
    try:
        xmp = reader.xmp_metadata
        if xmp is not None:
            xmp_bytes = None
            stream = getattr(xmp, "stream", None)
            if stream is not None:
                try:
                    xmp_bytes = stream.get_data()
                except Exception:
                    xmp_bytes = None
            if xmp_bytes:
                xmp_data = parse_xmp(xmp_bytes)
                result["has_xmp"] = True
            else:
                result["has_xmp"] = True
        else:
            result["has_xmp"] = False
    except Exception:
        result["has_xmp"] = False

    if xmp_data:
        result["xmp_create_date"] = parse_pdf_date(xmp_data.get("xmp_create_date")) or xmp_data.get("xmp_create_date")
        result["xmp_modify_date"] = parse_pdf_date(xmp_data.get("xmp_modify_date")) or xmp_data.get("xmp_modify_date")
        result["xmp_creator_tool"] = xmp_data.get("xmp_creator_tool")
        result["xmp_producer"] = xmp_data.get("xmp_producer")

    return result


def extract_image_metadata(raw: bytes, file_name: str, content_type: str) -> dict[str, Any]:
    """Best-effort EXIF extraction for JPG/PNG images."""
    from PIL import Image, ExifTags

    result: dict[str, Any] = {
        "file_name": file_name,
        "file_size_bytes": len(raw),
        "file_size_human": _human_size(len(raw)),
        "file_type": content_type or "image/*",
        "raw_info": {},
    }
    try:
        img = Image.open(io.BytesIO(raw))
        result["raw_info"]["format"] = img.format
        result["raw_info"]["mode"] = img.mode
        result["raw_info"]["width"], result["raw_info"]["height"] = img.size

        exif = {}
        try:
            raw_exif = img.getexif()
            for tag_id, value in raw_exif.items():
                tag = ExifTags.TAGS.get(tag_id, str(tag_id))
                try:
                    exif[tag] = _stringify(value)
                except Exception:
                    continue
        except Exception:
            exif = {}

        if exif:
            result["raw_info"]["exif"] = exif
            result["creator"] = exif.get("Software")
            result["producer"] = exif.get("Software")
            result["author"] = exif.get("Artist") or exif.get("Author")
            result["created_at"] = exif.get("DateTimeOriginal") or exif.get("DateTime")
            result["modified_at"] = exif.get("DateTime")
    except Exception as exc:
        result["raw_info"]["parse_error"] = str(exc)

    return result

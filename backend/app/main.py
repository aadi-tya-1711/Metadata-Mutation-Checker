"""FastAPI entrypoint for the Document Metadata Mutation Checker."""

from __future__ import annotations

import logging

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .analyzer import analyze_document, compare_documents
from .schemas import AnalysisReport, ComparisonReport

logger = logging.getLogger("metadata_checker")
logging.basicConfig(level=logging.INFO)


# Soft cap on uploads. PDFs are usually small; we reject anything wildly large
# before trying to parse it.
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB


app = FastAPI(
    title="Document Metadata Mutation Checker",
    description=(
        "A responsible metadata forensics service. Returns a structured "
        "report of metadata observations — never a verdict of tampering."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", summary="Service info")
def root() -> dict:
    return {
        "service": "Document Metadata Mutation Checker",
        "version": "1.0.0",
        "endpoints": {
            "POST /analyze": "Upload a PDF (or image) and receive a forensics report.",
            "POST /compare": "Upload two files and compare extracted metadata.",
            "GET  /health": "Liveness probe.",
        },
    }


@app.get("/health", summary="Liveness probe")
def health() -> dict:
    return {"status": "ok"}


@app.post(
    "/analyze",
    response_model=AnalysisReport,
    summary="Analyze a document and return a metadata forensics report",
)
async def analyze(file: UploadFile = File(...)) -> AnalysisReport:
    if file is None:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.",
        )

    try:
        report = analyze_document(
            raw=raw,
            file_name=file.filename or "uploaded",
            content_type=file.content_type,
        )
    except Exception as exc:
        logger.exception("Unhandled analyzer error: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="The analyzer failed unexpectedly. Please try a different file.",
        )

    return report


@app.post(
    "/compare",
    response_model=ComparisonReport,
    summary="Analyze and compare two documents",
)
async def compare(
    file_a: UploadFile = File(...),
    file_b: UploadFile = File(...),
) -> ComparisonReport:
    if file_a is None or file_b is None:
        raise HTTPException(status_code=400, detail="Both files are required.")

    raw_a = await file_a.read()
    raw_b = await file_b.read()
    if not raw_a or not raw_b:
        raise HTTPException(status_code=400, detail="Both files must be non-empty.")
    if len(raw_a) > MAX_UPLOAD_BYTES or len(raw_b) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Each file must be <= {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    try:
        report = compare_documents(
            raw_a=raw_a,
            file_name_a=file_a.filename or "file_a",
            content_type_a=file_a.content_type,
            raw_b=raw_b,
            file_name_b=file_b.filename or "file_b",
            content_type_b=file_b.content_type,
        )
    except Exception as exc:
        logger.exception("Unhandled compare error: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="The comparison failed unexpectedly. Please try different files.",
        )
    return report


@app.exception_handler(HTTPException)
async def _http_exception_handler(_request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

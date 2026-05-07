````md
# Document Metadata Mutation Checker

## Project Setup

### Backend

### Requirements
- Python 3.11+
- Virtual environment (recommended)

### Commands
```bash
python -m venv .venv

# Activate environment

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r backend/requirements.txt

cd backend
uvicorn app.main:app --reload
````

---

### Frontend

### Requirements

* Node.js 18+

### Commands

```bash
cd frontend
npm install
npm run dev
```

---

## Tools/Libraries Used

* **FastAPI**
* **Uvicorn**
* **pypdf**
* **pdfminer.six**
* **Pillow**
* **Pydantic v2**
* **React + Vite**

---

## Metadata Fields Extracted

### PDF Metadata

* File name, size, type
* PDF version, page count, encryption status
* Title, author, subject, keywords
* Creator and producer applications
* Creation and modification timestamps
* XMP metadata (creator tool, producer, dates)
* Incremental update count (`%%EOF` heuristic)
* Raw `/Info` dictionary snapshot

### Image Metadata (JPG/PNG)

* Dimensions and format
* Normalized EXIF fields (Software, Artist, DateTimeOriginal, etc.)

---

## Rules Implemented

* Missing or stripped metadata detection
* Missing creation/modification dates
* Modification date earlier than creation date
* Large gaps between creation and modification dates
* Creator vs producer inconsistencies
* Editor fingerprint detection (Adobe Acrobat, Canva, Foxit, etc.)
* XMP and `/Info` mismatch detection
* Incremental save/update detection
* Encryption detection
* Parser/structural error handling

---

## Scoring Logic

* **High** = 20 × confidence
* **Medium** = 10 × confidence
* **Low** = 5 × confidence

### Additional Safeguard

* If no Medium/High-confidence finding exists, the score is capped at **30**.

### Risk Levels

* **0–30** → Low
* **31–65** → Medium
* **66–100** → High

---

## Limitations

* Metadata alone cannot prove authenticity or manipulation
* No visual/content-level forensics or digital signature verification
* Encrypted PDFs restrict deeper inspection
* PDF date formats are inconsistent and sometimes malformed

---

## Improvements With More Time

* Object-level PDF structural diffing
* Exportable polished PDF reports
* Support for DOCX, XLSX, and ODT metadata analysis
* Full pytest-based unit testing suite
* Configurable YAML-based rule engine
* Multi-user authenticated dashboard with report history and audit trails

```
```

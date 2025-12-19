# TRACK B — DOCUMENT INTELLIGENCE & CERTIFICATE GENERATION

**Role:** “Notary’s document assistant”
**Owner:** You
**Dependency:** Consumes Track A output (`validation_result`) but can be built independently.

---

## OVERALL FLOW (Track B Mental Model)

1. Read customer folders (Drive or local)
2. Understand what documents exist
3. Extract structured data from documents
4. Normalize + reconcile extracted fields
5. Learn certificate templates & styles
6. Generate certificate drafts (Spanish)
7. Inject Track A legal result (OK / ERROR)
8. Export DOCX / PDF
9. Iterate with notary feedback

---

## MILESTONE-WISE EXECUTION PLAN (IN ORDER)

---

## MILESTONE 1 — PROJECT BASE & FOLDER MODEL (FOUNDATION)

**Goal:** Establish a predictable structure for customer data and certificates.

### What you implement

* Folder-to-customer mapping
* Customer identity abstraction (person vs company)
* Certificate history indexing

### Tools / Libraries

* Python 3.10+
* pathlib
* pydantic (schemas)
* sqlite / JSON files (lightweight storage)

### Tasks

* Define **Customer model**

  * customer_id
  * name
  * type: PERSON | COMPANY
  * folder_path
* Define **CertificateRecord**

  * certificate_type
  * institution
  * date
  * status (OK / ERROR)
  * source_files
* Scan folders:

  * Each folder = one customer
  * Index existing certificates (ERROR prefix matters)

### Output

* Structured customer registry
* Certificate history per customer

This milestone lets you **understand the client’s data reality**.

---

## MILESTONE 2 — GOOGLE DRIVE & FILE INGESTION

**Goal:** Reliably read PDFs, DOCXs, and images from Drive or uploads.

### Tools / Libraries

* Google Drive API
* google-auth
* google-api-python-client
* python-magic (file type detection)

### Tasks

* OAuth + Drive access (read-only)
* Fetch files per customer folder
* Download files locally with metadata
* Detect file type:

  * PDF
  * DOCX
  * JPG / PNG / scanned PDF

### Output

* Local working copy of all customer files
* Metadata index (filename, mime, size, modified date)

Track A is not involved here.

---

## MILESTONE 3 — DOCUMENT TEXT EXTRACTION (OCR + PARSING)

**Goal:** Convert all documents into usable Spanish text.

### Tools / Libraries

* pdfplumber (digital PDFs)
* python-docx
* pytesseract
* OpenCV (image preprocessing)
* Pillow

### Tasks

* Extract text from:

  * Digital PDFs
  * DOCX
* OCR flow for:

  * Scanned PDFs
  * JPG / PNG
* Store:

  * raw_text
  * page/section references
* Tag confidence level (OCR vs native)

### Output

* `extracted_text.json` per file
* Full Spanish text corpus per customer

This is the **core intelligence input** for the system.

---

## MILESTONE 4 — DATA FIELD EXTRACTION & NORMALIZATION

**Goal:** Convert messy text into structured facts.

### Tools / Libraries

* spaCy (Spanish model)
* regex
* dateparser
* rapidfuzz

### Fields to extract

* Full names
* Company names
* IDs (CI, RUT)
* Dates (issue / expiry)
* Institutions (BPS, MSP, Abitab, etc.)
* Roles (director, apoderado, representante)

### Tasks

* Entity extraction (NER + regex)
* Normalize:

  * Name capitalization
  * Date formats
  * ID formats
* Resolve duplicates / conflicts
* Mark uncertainty (low confidence fields)

### Output

```json
{
  "normalized_fields": {...},
  "conflicts": [...],
  "missing": [...]
}
```

This output is **exactly what Track A validates legally**.

---

## MILESTONE 5 — TEMPLATE DISCOVERY & STYLE LEARNING

**Goal:** Learn how each notary writes certificates.

### Tools / Libraries

* python-docx
* Jinja2
* difflib

### Tasks

* Identify certificate examples in folders
* Classify by:

  * Certificate type
  * Institution
* Extract:

  * Heading style
  * Paragraph structure
  * Phrases
  * Signature blocks
* Convert into Jinja2 templates
* Allow manual override templates

### Output

* Template library per notary
* Institution-specific templates

No law logic here — **pure formatting & style**.

---

## MILESTONE 6 — CERTIFICATE DRAFT GENERATION (SPANISH)

**Goal:** Generate human-quality certificate drafts.

### Tools / Libraries

* Jinja2
* python-docx
* reportlab or weasyprint (PDF)

### Tasks

* Input:

  * Normalized extracted data
  * Template
  * Track A validation result
* Generate:

  * Spanish certificate draft
* Inject:

  * ERROR banner if Track A says ERROR
  * Highlight problematic fields
* Maintain notarial tone

### Output

* Draft DOCX
* Draft PDF

This is where the notary **starts trusting the system**.

---

## MILESTONE 7 — TRACK A INTEGRATION (BOUNDARY-SAFE)

**Goal:** Consume legal decisions without interpreting law.

### Input from Track A

```json
{
  "status": "OK | ERROR",
  "issues": [
    {
      "field": "...",
      "reason": "...",
      "article": "..."
    }
  ]
}
```

### Tasks

* Display issues clearly
* Highlight affected paragraphs
* Prefix certificate title with ERROR when needed
* Never change status yourself

### Output

* Legally annotated draft
* Zero legal interpretation

This keeps responsibilities clean.

---

## MILESTONE 8 — FEEDBACK LOOP & TEMPLATE IMPROVEMENT

**Goal:** Let the system learn from the notary.

### Tools / Libraries

* diff tools
* simple feedback UI (later)

### Tasks

* Compare notary-edited vs generated version
* Track:

  * Phrase changes
  * Formatting changes
* Update templates incrementally
* Version templates safely

### Output

* Improved generation quality over time

---

## MILESTONE 9 — FINAL EXPORT & DELIVERY

**Goal:** Production-ready outputs.

### Tools / Libraries

* python-docx
* PDF renderer
* Google Drive API

### Tasks

* Export final DOCX / PDF
* Naming conventions
* Optional Drive upload
* Certificate archive update

### Output

* Downloadable legal-ready certificates

---

## DEPENDENCY SUMMARY (IMPORTANT)

* Track B **can be built independently**
* Only dependency:

  * Track A validation JSON
* Parallel development is safe
* No shared business logic

---

## DIFFICULTY (HONEST ASSESSMENT)

* Technically **moderate**
* Most complexity is:

  * Spanish documents
  * OCR quality
  * Template variance
* No deep AI research required
* Very deliverable-friendly

---

## WHAT YOU SHOULD BUILD FIRST (ACTION ORDER)

1. Folder indexing + customer model
2. Document ingestion
3. Text extraction + OCR
4. Field normalization
5. Template learning
6. Draft generation
7. Track A integration
